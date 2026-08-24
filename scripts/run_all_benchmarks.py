"""One-command reproduction script for all empirical benchmarks in Cut the Cake."""

from cut_the_cake.repair_benchmark import run_population_repair_benchmark, export_repair_benchmark_results
from cut_the_cake.vizdoom_fixtures import build_round11_benchmark_suite
from cut_the_cake.vizdoom_engine import run_population_benchmark

if __name__ == "__main__":
    print("================================================================")
    print("Cut the Cake: Reproducing Full Empirical Benchmark Pipeline")
    print("================================================================")

    print("\n[1/2] Running 60-Arena Round 11S Simulation Benchmark (9,000 episodes)...")
    suite = build_round11_benchmark_suite()
    sim_report = run_population_benchmark(suite, n_trials=30)
    print(f"Simulation Benchmark Complete: LOGFO-AUC = {sim_report.baseline_metrics['Tactical Margin M_tic'].logfo_cv_roc_auc:.4f}")

    print("\n[2/2] Running 50-Arena Inverse Tactical Repair & ViZDoom Benchmark...")
    repair_summary = run_population_repair_benchmark(target_margin_tics=2)
    export_repair_benchmark_results(repair_summary)
    print(f"Repair Benchmark Complete: Success Rate = {repair_summary.repair_success_rate*100:.1f}%, Engine Survival Flip Rate = {repair_summary.engine_survival_flip_rate*100:.1f}%")

    print("\nAll benchmarks reproduced successfully! Results written to results/")
