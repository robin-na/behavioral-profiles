"""Check release boundaries and agreement of archived tables with figure inputs."""
import json
from pathlib import Path
import re
import sys
import unittest

import numpy as np
import pandas as pd
from scipy.stats import spearmanr

ROOT = Path(__file__).resolve().parents[1]
REP = ROOT / "reproduction"
sys.path.insert(0, str(REP))
import reproduce


class ReleaseTests(unittest.TestCase):
    def test_input_integrity(self):
        reproduce.verify_inputs()

    def test_model_export_has_only_numerical_frequencies(self):
        d = pd.read_csv(REP / "data/model_outputs/simulated_outcome_counts.csv.gz")
        self.assertEqual(list(d), ['family', 'analysis', 'condition', 'simulated_value', 'count'])
        self.assertFalse(d.isna().any().any())
        self.assertTrue(np.isfinite(d.simulated_value).all())
        self.assertTrue((d['count'] > 0).all())
        self.assertTrue((d['count'] % 1 == 0).all())
        self.assertFalse(d.duplicated(['family', 'analysis', 'condition', 'simulated_value']).any())
        manifest = json.loads((REP / 'data/model_outputs/manifest.json').read_text())
        for item in manifest['datasets']:
            rows = d[(d.family == item['family']) & (d.analysis == item['analysis'])]
            self.assertEqual(int(rows['count'].sum()), item['outputs'])

    def test_no_record_identifiers_or_text_in_aggregate_columns(self):
        forbidden = {'participant_id', 'game_id', 'record_id', 'cohort_id', 'cohort_name',
                     'source_custom_id', 'target_game_id', 'profile_id', 'overall_persona',
                     'prompt', 'response', 'backstory', 'source_path', 'source', 'artifact_path'}
        for path in (REP / 'data').rglob('*.csv'):
            self.assertFalse(forbidden.intersection(pd.read_csv(path, nrows=0).columns), path.name)

    def test_no_local_paths_or_credentials_in_text_inputs(self):
        patterns = [r'/Users/', r'/home/', r'(?i)sk-(?:proj-)?[a-z0-9_-]{20,}', r'ghp_[A-Za-z0-9]{30,}']
        for path in (REP / 'data').rglob('*'):
            if path.suffix in {'.csv', '.tsv', '.json'}:
                for pattern in patterns:
                    self.assertIsNone(re.search(pattern, path.read_text()), path.name)

    def test_published_alignment_table_matches_all_figure_rows(self):
        table = next(t for t in json.loads((REP / 'data/published_tables.json').read_text()) if t['id'] == 'table_a7')
        lines = [r for r in table['rows'] if '&' in r]
        d = pd.read_csv(REP / 'data/main/figure3_heldout_results.csv')
        self.assertEqual(len(lines), len(d))
        conditions = ['selected_1', 'selected_2', 'complete', 'nemotron', 'twin', 'argyle', 'none']
        for i, line in enumerate(lines):
            cells = line.split('&')
            family = cells[0].strip().replace('--', '–')
            if family == '11–20':
                family = 'Generalized 11–20'
            row = d[(d.family == family) & (d.category == conditions[i % 7])].iloc[0]
            values = [float(n) for n in re.findall(r'-?\d+(?:\.\d+)?', cells[2])]
            np.testing.assert_allclose(values, [row.alignment, row.ci_low, row.ci_high], atol=.051)

    def test_rank_correlations_match_manuscript(self):
        for name, n, rho in [('pgg', 19, .884), ('chip_family', 15, .768), ('bounds1120', 7, .893)]:
            d = pd.read_csv(REP / 'data/main' / f'figure3_{name}_singleton_transfer.csv')
            self.assertEqual(len(d), n)
            self.assertAlmostEqual(spearmanr(d.learning_improvement, d.validation_improvement).statistic, rho, places=3)

    def test_learning_changes_match_losses_where_available(self):
        d = pd.read_csv(REP / 'data/appendix/appendix_learning_comparisons.csv').dropna(subset=['current_loss', 'candidate_loss', 'change'])
        self.assertGreater(len(d), 0)
        np.testing.assert_allclose(d.candidate_loss - d.current_loss, d.change, atol=1e-10)

    def test_cross_family_arrows_use_paired_intervals(self):
        d = pd.read_csv(REP / 'data/main/figure5_cross_domain_portability.csv')
        for row in d.itertuples():
            if row.comparison_status == 'better_than_no_profile':
                self.assertLess(row.paired_ci_high, 0)
            elif row.comparison_status == 'worse_than_no_profile':
                self.assertGreater(row.paired_ci_low, 0)
            elif pd.notna(row.paired_ci_low):
                self.assertLessEqual(row.paired_ci_low, 0)
                self.assertGreaterEqual(row.paired_ci_high, 0)

    def test_all_published_tables_present(self):
        tables = json.loads((REP / 'data/published_tables.json').read_text())
        self.assertEqual([t['id'] for t in tables], ['table_1', 'table_2'] + [f'table_a{i}' for i in range(1, 14)])


if __name__ == '__main__':
    unittest.main()
