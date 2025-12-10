#!/bin/bash

BASE_URL="${BASE_URL:-http://127.0.0.1:5000}"

echo "Seeding test events to $BASE_URL/webhook"
echo ""

send_event() {
    local event_type="$1"
    local itwin_id="$2"
    local imodel_id="$3"
    local itwin_name="$4"
    local imodel_name="$5"
    
    curl -s -X POST "$BASE_URL/webhook" \
        -H "Content-Type: application/json" \
        -d "{
            \"eventType\": \"$event_type\",
            \"timestamp\": \"$(date -u +%Y-%m-%dT%H:%M:%SZ)\",
            \"content\": {
                \"iTwinId\": \"$itwin_id\",
                \"iModelId\": \"$imodel_id\",
                \"iTwinName\": \"$itwin_name\",
                \"iModelName\": \"$imodel_name\"
            }
        }" > /dev/null
    
    echo "Sent: $event_type"
}

send_event "iTwins.iTwinCreated.v1" "itwin-001-abc" "" "Highway 101 Project" ""
send_event "iModels.iModelCreated.v1" "itwin-001-abc" "imodel-101-xyz" "Highway 101 Project" "Bridge Design Model"
send_event "iModels.namedVersionCreated.v1" "itwin-001-abc" "imodel-101-xyz" "Highway 101 Project" "Bridge Design Model"
send_event "accessControl.memberAdded.v1" "itwin-001-abc" "" "Highway 101 Project" ""
send_event "synchronization.jobCompleted.v1" "itwin-001-abc" "imodel-101-xyz" "Highway 101 Project" "Bridge Design Model"

send_event "iTwins.iTwinCreated.v1" "itwin-002-def" "" "Downtown Tower" ""
send_event "iModels.iModelCreated.v1" "itwin-002-def" "imodel-202-uvw" "Downtown Tower" "Structural Analysis"
send_event "iModels.changesReady.v1" "itwin-002-def" "imodel-202-uvw" "Downtown Tower" "Structural Analysis"
send_event "issues.issueCreated.v1" "itwin-002-def" "imodel-202-uvw" "Downtown Tower" "Structural Analysis"
send_event "forms.formCreated.v1" "itwin-002-def" "" "Downtown Tower" ""

send_event "iModels.iModelCreated.v1" "itwin-003-ghi" "imodel-303-rst" "Water Treatment Plant" "Pipeline Network"
send_event "realityModeling.jobCompleted.v1" "itwin-003-ghi" "imodel-303-rst" "Water Treatment Plant" "Pipeline Network"
send_event "transformations.jobCompleted.v1" "itwin-003-ghi" "imodel-303-rst" "Water Treatment Plant" "Pipeline Network"
send_event "accessControl.roleAssigned.v1" "itwin-003-ghi" "" "Water Treatment Plant" ""
send_event "iModels.namedVersionCreated.v1" "itwin-003-ghi" "imodel-303-rst" "Water Treatment Plant" "Pipeline Network"

send_event "iTwins.iTwinCreated.v1" "itwin-004-jkl" "" "Solar Farm Alpha" ""
send_event "iModels.iModelCreated.v1" "itwin-004-jkl" "imodel-404-opq" "Solar Farm Alpha" "Panel Layout"
send_event "changedElements.jobCompleted.v1" "itwin-004-jkl" "imodel-404-opq" "Solar Farm Alpha" "Panel Layout"
send_event "issues.issueUpdated.v1" "itwin-004-jkl" "imodel-404-opq" "Solar Farm Alpha" "Panel Layout"
send_event "accessControl.memberRemoved.v1" "itwin-004-jkl" "" "Solar Farm Alpha" ""

echo ""
echo "Done! Seeded 20 test events."
echo "Visit $BASE_URL/dashboard to view the dashboard."
