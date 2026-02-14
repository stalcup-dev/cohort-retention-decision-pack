param(
  [string]$NotebookPath = "notebooks/cohort_retention_story.ipynb",
  [string]$OutputDir = "exports",
  [string]$OutputName = "cohort_retention_story",
  [switch]$Execute = $true
)

$env:JUPYTER_ALLOW_INSECURE_WRITES = "true"

$execFlag = ""
if ($Execute) {
  $execFlag = "--execute"
}

py -3 -m jupyter nbconvert $NotebookPath `
  --to html `
  --output-dir $OutputDir `
  --output $OutputName `
  --no-input `
  --TagRemovePreprocessor.enabled=True `
  --TagRemovePreprocessor.remove_input_tags="['hide_code']" `
  $execFlag

if ($LASTEXITCODE -ne 0) {
  exit $LASTEXITCODE
}

py -3 scripts/build_artifact_manifest.py --stamp-html
