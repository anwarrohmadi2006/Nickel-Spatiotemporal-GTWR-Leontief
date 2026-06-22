# Task List: Super Panel Integration

- `[x]` 1. **Data Inspection**: Analyze the schema of CREA and IEEFA tables to identify relevant columns (Agriculture PDRB, Emission Intensity, etc.).
- `[x]` 2. **Build Super Panel Script**: Create `build_super_panel.py` to extract, clean, and merge data from all 56 CSV files into a single rich dataset.
- `[x]` 3. **Run Super Panel Builder**: Execute the script to generate `SpatioTemporal_SuperPanel_N212.csv`.
- `[x]` 4. **Update Showdown Script**: Modify `run_ultimate_showdown.py` to ingest the new super panel features and predict the specific Agriculture sector impact.
- `[x]` 5. **Execution & Verification**: Run the updated showdown script and ensure GTWR performs flawlessly.
- `[x]` 6. **Walkthrough**: Create a walkthrough artifact explaining the new data pipeline.
- `[x]` 7. **Remove Synthetic Noise**: Modify `build_super_panel.py` to remove `np.random.normal()` and calculate `Agri_Loss_RpMiliar` strictly deterministically.
- `[x]` 8. **Remove Hardcoded Metrics**: Modify `run_ultimate_showdown.py` to print real computed R2 values instead of hardcoded ones.
- `[x]` 9. **Verify & Document**: Run both scripts, verify real performance, and update the walkthrough.
- `[x]` 10. **Enrich Dataset Extraction**: Modify `build_super_panel.py` to extract 4 other sectors, 3 health variables, and non-coal MW specs.
- `[x]` 11. **Implement GA Feature Selection**: Create `run_ga_feature_selection.py` to perform genetic algorithm optimization.
- `[x]` 12. **Update Ultimate Showdown**: Modify `run_ultimate_showdown.py` to use the enriched dataset and the optimal features selected by GA.
- `[x]` 13. **Verify & Document Showdown**: Run the updated scripts and verify final dynamic performance metrics.
