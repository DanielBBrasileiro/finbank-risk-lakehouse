use anyhow::{anyhow, Result};
use clap::{Parser, Subcommand};
use serde::Deserialize;
use std::collections::{HashMap, HashSet};
use std::fs;

#[derive(Parser)]
#[command(name = "finbank-validator")]
#[command(about = "Fast CSV schema validator for the FinBank Risk Lakehouse project")]
struct Cli {
    #[command(subcommand)]
    command: Commands,
}

#[derive(Subcommand)]
enum Commands {
    Validate {
        #[arg(long)]
        input: String,

        #[arg(long)]
        schema: String,
    },
}

#[derive(Debug, Deserialize)]
struct Schema {
    name: String,
    required_columns: Vec<String>,
    not_null: Vec<String>,
    unique: Vec<String>,
    #[serde(default)]
    types: HashMap<String, String>,
    #[serde(default)]
    ranges: HashMap<String, RangeRule>,
    #[serde(default)]
    accepted_values: HashMap<String, HashSet<String>>,
}

#[derive(Debug, Deserialize)]
struct RangeRule {
    min: Option<f64>,
    max: Option<f64>,
}

fn main() -> Result<()> {
    let cli = Cli::parse();

    match cli.command {
        Commands::Validate { input, schema } => validate_csv(&input, &schema),
    }
}

fn validate_csv(input_path: &str, schema_path: &str) -> Result<()> {
    let schema_text = fs::read_to_string(schema_path)?;
    let schema: Schema = serde_json::from_str(&schema_text)?;

    let mut reader = csv::Reader::from_path(input_path)?;
    let headers = reader.headers()?.clone();

    let header_set: HashSet<String> = headers.iter().map(|s| s.to_string()).collect();

    let mut errors: Vec<String> = Vec::new();

    for col in &schema.required_columns {
        if !header_set.contains(col) {
            errors.push(format!("Missing required column: {}", col));
        }
    }

    let mut unique_trackers: HashMap<String, HashSet<String>> = HashMap::new();
    for col in &schema.unique {
        unique_trackers.insert(col.clone(), HashSet::new());
    }

    let mut row_count = 0usize;

    for result in reader.deserialize::<HashMap<String, String>>() {
        let row = result?;
        row_count += 1;

        for col in &schema.not_null {
            let value = row.get(col).map(|v| v.trim()).unwrap_or("");
            if value.is_empty() {
                errors.push(format!("Row {}: null/empty value in '{}'", row_count, col));
            }
        }

        for col in &schema.unique {
            if let Some(value) = row.get(col) {
                if let Some(seen) = unique_trackers.get_mut(col) {
                    if seen.contains(value) {
                        errors.push(format!("Row {}: duplicate value '{}' in '{}'", row_count, value, col));
                    } else {
                        seen.insert(value.clone());
                    }
                }
            }
        }

        for (col, expected_type) in &schema.types {
            let value = row.get(col).map(|item| item.trim()).unwrap_or("");
            if !value.is_empty() && !matches_type(value, expected_type) {
                errors.push(format!(
                    "Row {}: value '{}' in '{}' is not {}",
                    row_count, value, col, expected_type
                ));
            }
        }

        for (col, rule) in &schema.ranges {
            let value = row.get(col).map(|item| item.trim()).unwrap_or("");
            if value.is_empty() {
                continue;
            }
            if let Ok(number) = value.parse::<f64>() {
                if rule.min.is_some_and(|minimum| number < minimum)
                    || rule.max.is_some_and(|maximum| number > maximum)
                {
                    errors.push(format!(
                        "Row {}: value '{}' in '{}' is outside the allowed range",
                        row_count, value, col
                    ));
                }
            }
        }

        for (col, accepted) in &schema.accepted_values {
            let value = row.get(col).map(|item| item.trim()).unwrap_or("");
            if !value.is_empty() && !accepted.contains(value) {
                errors.push(format!(
                    "Row {}: value '{}' in '{}' is outside the accepted domain",
                    row_count, value, col
                ));
            }
        }
    }

    if errors.is_empty() {
        println!("Validation passed for '{}'. Rows checked: {}", schema.name, row_count);
        Ok(())
    } else {
        eprintln!("Validation failed for '{}'. Errors: {}", schema.name, errors.len());
        for err in errors.iter().take(50) {
            eprintln!("- {}", err);
        }
        if errors.len() > 50 {
            eprintln!("... and {} more errors", errors.len() - 50);
        }
        Err(anyhow!("CSV validation failed"))
    }
}

fn matches_type(value: &str, expected_type: &str) -> bool {
    match expected_type {
        "integer" => value.parse::<i64>().is_ok(),
        "number" => value.parse::<f64>().is_ok(),
        "boolean" => matches!(value.to_ascii_lowercase().as_str(), "true" | "false"),
        "string" => true,
        _ => false,
    }
}

#[cfg(test)]
mod tests {
    use super::*;
    use std::path::PathBuf;
    use std::time::{SystemTime, UNIX_EPOCH};

    fn fixture_paths(test_name: &str) -> (PathBuf, PathBuf) {
        let nonce = SystemTime::now()
            .duration_since(UNIX_EPOCH)
            .expect("system time")
            .as_nanos();
        let directory = std::env::temp_dir().join(format!(
            "finbank-validator-{}-{}-{}",
            test_name,
            std::process::id(),
            nonce
        ));
        fs::create_dir_all(&directory).expect("fixture directory");
        (directory.join("input.csv"), directory.join("schema.json"))
    }

    fn write_schema(path: &PathBuf) {
        fs::write(
            path,
            r#"{
                "name": "test_records",
                "required_columns": ["id", "score", "status", "active"],
                "not_null": ["id", "score", "status", "active"],
                "unique": ["id"],
                "types": {"score": "integer", "active": "boolean"},
                "ranges": {"score": {"min": 0, "max": 1000}},
                "accepted_values": {"status": ["ACTIVE", "BLOCKED"]}
            }"#,
        )
        .expect("schema fixture");
    }

    #[test]
    fn accepts_rows_that_satisfy_the_contract() {
        let (input, schema) = fixture_paths("valid");
        write_schema(&schema);
        fs::write(&input, "id,score,status,active\n1,850,ACTIVE,true\n")
            .expect("CSV fixture");

        assert!(validate_csv(input.to_str().unwrap(), schema.to_str().unwrap()).is_ok());
    }

    #[test]
    fn rejects_duplicate_invalid_type_range_and_domain() {
        let (input, schema) = fixture_paths("invalid");
        write_schema(&schema);
        fs::write(
            &input,
            "id,score,status,active\n1,1200,UNKNOWN,yes\n1,not-a-number,ACTIVE,false\n",
        )
        .expect("CSV fixture");

        assert!(validate_csv(input.to_str().unwrap(), schema.to_str().unwrap()).is_err());
    }
}
