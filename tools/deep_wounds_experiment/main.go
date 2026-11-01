package main

import (
	"encoding/json"
	"fmt"
	"os"

	"github.com/wowsims/forever/sim/common"
	"github.com/wowsims/forever/sim/core"
	"github.com/wowsims/forever/sim/core/proto"
	"github.com/wowsims/forever/sim/warrior/dps"
	"google.golang.org/protobuf/encoding/protojson"
)

func main() {
	if err := run(); err != nil {
		fmt.Fprintln(os.Stderr, err)
		os.Exit(1)
	}
}

func run() error {
	if len(os.Args) != 3 {
		return fmt.Errorf("usage: experiment input.json output.json")
	}
	data, err := os.ReadFile(os.Args[1])
	if err != nil {
		return err
	}
	var input struct {
		Cases []struct {
			Name string
			Ham bool
			Request json.RawMessage
		}
	}
	if err := json.Unmarshal(data, &input); err != nil {
		return err
	}
	if len(input.Cases) < 1 || len(input.Cases) > 200 {
		return fmt.Errorf("need 1 to 200 prepared cases, got %d", len(input.Cases))
	}
	dps.RegisterDpsWarrior()
	common.RegisterAllEffects()
	rows := make([]map[string]any, 0, len(input.Cases))
	for _, entry := range input.Cases {
		request := &proto.RaidSimRequest{}
		if err := protojson.Unmarshal(entry.Request, request); err != nil {
			return fmt.Errorf("%s: %w", entry.Name, err)
		}
		preflight := core.ComputeStats(&proto.ComputeStatsRequest{Raid: request.Raid, Encounter: request.Encounter})
		statsJSON, err := protojson.Marshal(preflight)
		if err != nil {
			return err
		}
		if os.Getenv("EXPERIMENT_REQUIRE_CLEAN_APL") == "1" {
			var value any
			if err := json.Unmarshal(statsJSON, &value); err != nil {
				return err
			}
			if warnings := rotationWarnings(value); len(warnings) > 0 {
				return fmt.Errorf("%s: rotation warnings: %v", entry.Name, warnings)
			}
		}
		result := core.RunRaidSim(request)
		if result.Error != nil {
			return fmt.Errorf("%s: %s", entry.Name, result.Error.Message)
		}
		if result.IterationsDone != request.SimOptions.Iterations {
			return fmt.Errorf("%s: completed %d iterations, want %d", entry.Name, result.IterationsDone, request.SimOptions.Iterations)
		}
		resultJSON, err := protojson.Marshal(result)
		if err != nil {
			return err
		}
		rows = append(rows, map[string]any{"name": entry.Name, "ham": entry.Ham, "request": entry.Request, "preflightStats": json.RawMessage(statsJSON), "raw": json.RawMessage(resultJSON)})
		fmt.Printf("%s: %.6f DPS (%d iterations)\n", entry.Name, result.RaidMetrics.Dps.Avg, result.IterationsDone)
	}
	output := map[string]any{"source": os.Getenv("EXPERIMENT_SOURCE"), "mode": "own-hand-source-comparison", "results": rows}
	bytes, err := json.MarshalIndent(output, "", "  ")
	if err != nil {
		return err
	}
	return os.WriteFile(os.Args[2], bytes, 0644)
}

func rotationWarnings(value any) []string {
	var warnings []string
	switch node := value.(type) {
	case map[string]any:
		if message, ok := node["validation"].(string); ok && message != "" && (node["logLevel"] == "Warning" || node["logLevel"] == "Error") {
			warnings = append(warnings, message)
		}
		for _, child := range node {
			warnings = append(warnings, rotationWarnings(child)...)
		}
	case []any:
		for _, child := range node {
			warnings = append(warnings, rotationWarnings(child)...)
		}
	}
	return warnings
}
