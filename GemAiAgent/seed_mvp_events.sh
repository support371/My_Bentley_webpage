#!/usr/bin/env bash
set -e

BASE_URL="\${BASE_URL:-https://bentley-itwins.replit.dev}"

echo "Seeding MVP test events into: \$BASE_URL/webhook"

send_event () {
  local eventType="\$1"
  local itwinId="\$2"
  local imodelId="\$3"
  local itwinName="\$4"
  local imodelName="\$5"
  local versionName="\$6"

  payload=\$(cat << JSON
{
  "eventType": "\$eventType",
  "payload": {
    "iTwinId": "\$itwinId",
    "iModelId": "\$imodelId",
    "iTwinName": "\$itwinName",
    "iModelName": "\$imodelName",
    "user": "system@test",
    "versionName": "\$versionName",
    "changeSetId": "changeset-\$RANDOM"
  }
}
JSON
)

  code=\$(curl -s -o /dev/null -w "%{http_code}" \
    -X POST "\$BASE_URL/webhook" \
    -H "Content-Type: application/json" \
    -d "\$payload" || true)

  if [ "\$code" = "200" ] || [ "\$code" = "201" ] || [ "\$code" = "202" ]; then
    echo "✅ Sent \$eventType"
  else
    echo "⚠️  Failed \$eventType HTTP \$code"
  fi
}

ITWIN_ID="itwin-demo-001"
IMODEL_ID="imodel-demo-001"

send_event "iModels.iModelCreated.v1" "\$ITWIN_ID" "\$IMODEL_ID" "Demo iTwin" "Demo iModel" ""
sleep 0.3
send_event "iModels.changesReady.v1" "\$ITWIN_ID" "\$IMODEL_ID" "Demo iTwin" "Demo iModel" ""
sleep 0.3
send_event "iModels.namedVersionCreated.v1" "\$ITWIN_ID" "\$IMODEL_ID" "Demo iTwin" "Demo iModel" "v1.0"
sleep 0.3
send_event "iModels.iModelDeleted.v1" "\$ITWIN_ID" "\$IMODEL_ID" "Demo iTwin" "Demo iModel" ""

echo "----------------------------------------"
echo "Now re-check /events and /dashboard/feed"
echo "----------------------------------------"
