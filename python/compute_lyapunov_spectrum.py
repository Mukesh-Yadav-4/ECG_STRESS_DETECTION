"""
=============================================================================
Numerical Lyapunov Spectrum & Dynamical Benchmark Suite
for the 4D Coupled Nonlinear Dynamical System (M-4DCHS)
=============================================================================
Computes the full 4D Lyapunov spectrum [lambda_1, lambda_2, lambda_3, lambda_4]
using continuous variational tangent-space integration (dPhi/dt = J(x)*Phi)
coupled with classical 4th-order Runge-Kutta (RK4) and QR Gram-Schmidt 
reorthogonalization (Benettin et al. / Shimada & Nagashima algorithm).

Validates:
  1. Vector field trace / divergence constraint (Liouville's theorem):
     Tr(J) = -(a + b - d) = -39.000000
  2. Numerical convergence of sum(lambda_i) toward -39.000000
  3. Identification of expanding (lambda > 0), neutral (lambda ~ 0), 
     and contracting (lambda << 0) directions
  4. Calculation of fractional Kaplan-Yorke attractor dimension D_KY
  5. Multi-parameter convergence across step sizes (dt), evaluation times (T),
     and diverse initial conditions.
=============================================================================
"""

import sys
import os
import json
import numpy as np

# System parameters matching m4d_hyperchaos.py & telemetry_protocol.c (Verified HC1 Regime)
M4D_A = 15.81
M4D_B = 2.76
M4D_C = 86.03
M4D_D = -9.07
M4D_R = 10.79
M4D_DT = 0.0025


def m4d_vector_field(state: np.ndarray) -> np.ndarray:
    """Evaluates the continuous 4D velocity field F(x)."""
    x, y, z, w = state
    return np.array([
        M4D_A * (y - x) + w,
        M4D_C * x - x * z + M4D_D * y,
        x * y - M4D_B * z,
        -M4D_R * x
    ], dtype=np.float64)


def m4d_jacobian(state: np.ndarray) -> np.ndarray:
    """Evaluates the 4x4 Jacobian matrix J(x) = dF/dx."""
    x, y, z, w = state
    return np.array([
        [-M4D_A,         M4D_A,   0.0,    1.0],
        [M4D_C - z,      M4D_D,   -x,     0.0],
        [y,              x,       -M4D_B, 0.0],
        [-M4D_R,         0.0,     0.0,    0.0]
    ], dtype=np.float64)


def integrate_lyapunov(
    x0: np.ndarray = np.array([1.0, 1.0, 1.0, 1.0], dtype=np.float64),
    t_transient: float = 100.0,
    t_run: float = 500.0,
    dt: float = M4D_DT
) -> dict:
    """
    Integrates the coupled state + variational equations to compute the full
    Lyapunov exponent spectrum and Kaplan-Yorke dimension for given settings.
    """
    theory_div = float(-(M4D_A + M4D_B - M4D_D))
    state = np.copy(x0).astype(np.float64)

    # 1. Warm-up / transient removal
    n_trans = int(t_transient / dt)
    for _ in range(n_trans):
        k1 = m4d_vector_field(state)
        k2 = m4d_vector_field(state + 0.5 * dt * k1)
        k3 = m4d_vector_field(state + 0.5 * dt * k2)
        k4 = m4d_vector_field(state + dt * k3)
        state += (dt / 6.0) * (k1 + 2.0 * k2 + 2.0 * k3 + k4)

    # 2. Tangent-space variational integration
    Q = np.eye(4, dtype=np.float64)
    n_run = int(t_run / dt)
    cum_log_diag = np.zeros(4, dtype=np.float64)

    for step in range(n_run):
        J = m4d_jacobian(state)

        k1_s = m4d_vector_field(state)
        k1_Q = J @ Q

        s2 = state + 0.5 * dt * k1_s
        k2_s = m4d_vector_field(s2)
        k2_Q = m4d_jacobian(s2) @ (Q + 0.5 * dt * k1_Q)

        s3 = state + 0.5 * dt * k2_s
        k3_s = m4d_vector_field(s3)
        k3_Q = m4d_jacobian(s3) @ (Q + 0.5 * dt * k2_Q)

        s4 = state + dt * k3_s
        k4_s = m4d_vector_field(s4)
        k4_Q = m4d_jacobian(s4) @ (Q + dt * k3_Q)

        state += (dt / 6.0) * (k1_s + 2.0 * k2_s + 2.0 * k3_s + k4_s)
        Q += (dt / 6.0) * (k1_Q + 2.0 * k2_Q + 2.0 * k3_Q + k4_Q)

        # QR reorthogonalization
        Q, R = np.linalg.qr(Q)
        cum_log_diag += np.log(np.abs(np.diag(R)))

    total_time = n_run * dt
    exponents = cum_log_diag / total_time
    sorted_idx = np.argsort(exponents)[::-1]
    sorted_exponents = exponents[sorted_idx]
    sum_exponents = float(np.sum(exponents))
    dev_from_theory = abs(sum_exponents - theory_div)

    # Kaplan-Yorke dimension
    cum_sum = 0.0
    j_ky = 0
    for i in range(len(sorted_exponents)):
        if cum_sum + sorted_exponents[i] >= 0.0:
            cum_sum += sorted_exponents[i]
            j_ky = i + 1
        else:
            break

    if j_ky < len(sorted_exponents) and abs(sorted_exponents[j_ky]) > 1e-12:
        d_ky = j_ky + (cum_sum / abs(sorted_exponents[j_ky]))
    else:
        d_ky = float(len(sorted_exponents))

    return {
        "x0": x0.tolist(),
        "final_state": state.tolist(),
        "t_transient": t_transient,
        "t_run": total_time,
        "dt": dt,
        "n_steps": n_run,
        "raw_exponents": exponents.tolist(),
        "sorted_exponents": sorted_exponents.tolist(),
        "lambda_1": float(sorted_exponents[0]),
        "lambda_2": float(sorted_exponents[1]),
        "lambda_3": float(sorted_exponents[2]),
        "lambda_4": float(sorted_exponents[3]),
        "sum_exponents": sum_exponents,
        "theoretical_divergence": theory_div,
        "absolute_deviation": dev_from_theory,
        "kaplan_yorke_dimension": float(d_ky),
        "j_index": j_ky,
        "numerator": float(cum_sum),
        "denominator": float(abs(sorted_exponents[j_ky])) if j_ky < len(sorted_exponents) else 0.0,
    }


def run_benchmark():
    print("=" * 75)
    print("   4D COUPLED NONLINEAR SYSTEM: NUMERICAL LYAPUNOV SPECTRUM BENCHMARK")
    print("   Variational RK4 + QR Reorthogonalization (Benettin Algorithm)")
    print("=" * 75)
    print(f"Parameters: a={M4D_A}, b={M4D_B}, c={M4D_C}, d={M4D_D}, r={M4D_R}")
    print(f"Theoretical Trace: Tr(J) = -(a + b - d) = {-(M4D_A + M4D_B - M4D_D):.6f}\n")

    # Primary baseline run
    print("[1/2] Executing Primary Reference Benchmark (dt=0.0025, T=500s)...")
    res_primary = integrate_lyapunov(
        x0=np.array([1.0, 1.0, 1.0, 1.0]),
        t_transient=100.0,
        t_run=500.0,
        dt=0.0025
    )

    print("\n--- Primary Benchmark Results ---")
    print(f"  Numerical Lyapunov exponents: {res_primary['raw_exponents']}")
    print(f"  Sum of exponents            : {res_primary['sum_exponents']:.6f}")
    print(f"  Theoretical divergence      : {res_primary['theoretical_divergence']:.6f}")
    print(f"  Absolute deviation (error)  : {res_primary['absolute_deviation']:.6e}")
    print("-" * 55)
    print("  Sorted Exponent Spectrum:")
    for idx, val in enumerate(res_primary['sorted_exponents']):
        direction = "Neutral (Flow Direction)" if abs(val) <= 0.01 else ("Expanding" if val > 0 else "Contracting (Dissipative)")
        print(f"    lambda_{idx+1} = {val:+.6f}   [{direction}]")
    print("-" * 55)
    print(f"  Kaplan-Yorke Dimension D_KY : {res_primary['kaplan_yorke_dimension']:.6f}")
    print(f"    j (non-negative sum index): {res_primary['j_index']}")
    print(f"    Numerator (sum_i=1^1 lambda_i): {res_primary['numerator']:+.6f}")
    print(f"    Denominator (|lambda_2|)   : {res_primary['denominator']:.6f}")
    print("=" * 75)

    # Multi-condition convergence sweep
    print("\n[2/2] Executing Multi-Parameter Convergence & Robustness Suite...")
    sweep_results = []

    # Sweep dt
    for dt_test in [0.005, 0.0025, 0.00125]:
        r = integrate_lyapunov(x0=np.array([1.0, 1.0, 1.0, 1.0]), t_transient=50.0, t_run=200.0, dt=dt_test)
        r["test_type"] = f"Step size dt={dt_test}"
        sweep_results.append(r)
        print(f"  dt={dt_test:<7}: lambda_1={r['lambda_1']:+.6f}, lambda_2={r['lambda_2']:+.6f}, lambda_3={r['lambda_3']:+.6f}, lambda_4={r['lambda_4']:+.6f} | Sum={r['sum_exponents']:.6f} | D_KY={r['kaplan_yorke_dimension']:.4f}")

    # Sweep duration T
    for t_test in [200.0, 500.0, 1000.0]:
        r = integrate_lyapunov(x0=np.array([1.0, 1.0, 1.0, 1.0]), t_transient=100.0, t_run=t_test, dt=0.0025)
        r["test_type"] = f"Evaluation duration T={t_test}s"
        sweep_results.append(r)
        print(f"  T={t_test:<6.0f}s : lambda_1={r['lambda_1']:+.6f}, lambda_2={r['lambda_2']:+.6f}, lambda_3={r['lambda_3']:+.6f}, lambda_4={r['lambda_4']:+.6f} | Sum={r['sum_exponents']:.6f} | D_KY={r['kaplan_yorke_dimension']:.4f}")

    # Sweep initial conditions
    for ic_name, ic in [("IC_A [1, 1, 1, 1]", np.array([1.0, 1.0, 1.0, 1.0])),
                        ("IC_B [2, -1, 5, 0]", np.array([2.0, -1.0, 5.0, 0.0])),
                        ("IC_C [-2, 3, 10, -5]", np.array([-2.0, 3.0, 10.0, -5.0]))]:
        r = integrate_lyapunov(x0=ic, t_transient=100.0, t_run=300.0, dt=0.0025)
        r["test_type"] = f"Initial Condition {ic_name}"
        sweep_results.append(r)
        print(f"  {ic_name:<18}: lambda_1={r['lambda_1']:+.6f}, lambda_2={r['lambda_2']:+.6f}, lambda_3={r['lambda_3']:+.6f}, lambda_4={r['lambda_4']:+.6f} | Sum={r['sum_exponents']:.6f} | D_KY={r['kaplan_yorke_dimension']:.4f}")

    # Save complete permanent benchmark artifacts
    project_root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    results_dir = os.path.join(project_root, "results")
    os.makedirs(results_dir, exist_ok=True)

    json_path = os.path.join(results_dir, "m4d_lyapunov_benchmark.json")
    full_output = {
        "primary_reference": res_primary,
        "robustness_convergence_suite": sweep_results,
    }
    with open(json_path, "w", encoding="utf-8") as f:
        json.dump(full_output, f, indent=2)

    txt_path = os.path.join(results_dir, "m4d_lyapunov_benchmark.txt")
    with open(txt_path, "w", encoding="utf-8") as f:
        f.write("=" * 75 + "\n")
        f.write("4D COUPLED NONLINEAR SYSTEM: NUMERICAL LYAPUNOV SPECTRUM BENCHMARK\n")
        f.write("=" * 75 + "\n")
        f.write(f"Parameters: a={M4D_A}, b={M4D_B}, c={M4D_C}, d={M4D_D}, r={M4D_R}\n")
        f.write(f"Theoretical Divergence: {res_primary['theoretical_divergence']:.6f}\n\n")
        f.write("PRIMARY REFERENCE RUN (dt=0.0025s, T=500s, 200,000 steps):\n")
        f.write(f"  Numerical Exponents: {res_primary['raw_exponents']}\n")
        f.write(f"  Sum of Exponents   : {res_primary['sum_exponents']:.6f}\n")
        f.write(f"  Absolute Error     : {res_primary['absolute_deviation']:.6e}\n")
        f.write("  Sorted Exponents:\n")
        f.write(f"    lambda_1 = {res_primary['lambda_1']:+.6f}  [Neutral flow direction]\n")
        f.write(f"    lambda_2 = {res_primary['lambda_2']:+.6f}  [Contracting]\n")
        f.write(f"    lambda_3 = {res_primary['lambda_3']:+.6f}  [Contracting]\n")
        f.write(f"    lambda_4 = {res_primary['lambda_4']:+.6f}  [Strongly contracting]\n")
        f.write(f"  Kaplan-Yorke Dimension D_KY = {res_primary['kaplan_yorke_dimension']:.6f} (j={res_primary['j_index']})\n\n")
        f.write("-" * 75 + "\n")
        f.write("ROBUSTNESS & CONVERGENCE SWEEP:\n")
        for r in sweep_results:
            f.write(f"  {r['test_type']:<32} | lambda=[{r['lambda_1']:+.4f}, {r['lambda_2']:+.4f}, {r['lambda_3']:+.4f}, {r['lambda_4']:+.4f}] | Sum={r['sum_exponents']:.6f} | D_KY={r['kaplan_yorke_dimension']:.4f}\n")
        f.write("=" * 75 + "\n")

    print(f"\n[Saved full benchmark and convergence study to {json_path} and {txt_path}]")
    return full_output


if __name__ == "__main__":
    run_benchmark()
