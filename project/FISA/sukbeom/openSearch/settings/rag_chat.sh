#!bin/bash

curl -XPUT "http://localhost:9300/_cluster/settings" -H 'Content-Type: application/json' -d'
{
    "persistent": {
        "plugins.ml_commons.only_run_on_ml_node": false,
        "plugins.ml_commons.native_memory_threshold": 100,
        "plugins.ml_commons.agent_framework_enabled": true
    }
}
'