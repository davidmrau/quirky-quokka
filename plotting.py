"""
Define plotting functions here.
"""

# STD
import os

# EXT
import numpy as np
import matplotlib.pyplot as plt
import matplotlib

# PROJECT
from analyze import test_difference

if os.environ.get('DISPLAY', '') == '':
    print('no display found. Using non-interactive Agg backend')
    matplotlib.use('Agg')


def smooth(x, N):
    cumsum = np.cumsum(np.insert(x, 0, 0))
    return (cumsum[N:] - cumsum[:-N]) / float(N)


def plot_exp_performance(exps, path):
    for exp, env_name in exps:
        plt.figure()

        for episode_duration, exp_name in exp:
            plt.plot(smooth(episode_duration, 10), label=exp_name)
        plt.title('Episode durations per episode in ' + env_name)
        plt.legend()
        plt.savefig(f"{path}/{env_name}.png")


def plot_exps_with_intervals(q_data: np.array, dq_data: np.array, file_name, title=None, significant_values=None,
                             true_q: float=None, true_dq: float=None, smooth_curves=False):
    """
    Plot scores with intervals. Expects a K x D matrix with K trials with D data points each.
    """
    assert q_data.shape[0] > 1 and dq_data.shape[0] > 1, "At least two trials per model are necessary to create this plot!"

    def get_curves(data):
        median = np.median(data, axis=0)

        # Average of the two most extreme values to get upper / lower bounds
        upper = np.mean(np.sort(data, axis=0)[-2:, :], axis=0)
        lower = np.mean(np.sort(data, axis=0)[:2, :], axis=0)

        if smooth_curves:
            return smooth(lower, 10), smooth(median, 10), smooth(upper, 10)
        else:
            return lower, median, upper

    # Get the median, lower and upper curves
    q_lower, q_median, q_upper = get_curves(q_data)
    dq_lower, dq_median, dq_upper = get_curves(dq_data)

    # Plot everything
    x = np.arange(0, q_lower.shape[0])
    plt.plot(q_median, label="DQN", color="firebrick")
    plt.fill_between(x, q_upper, q_median, facecolor="lightcoral", alpha=0.6)
    plt.fill_between(x, q_median, q_lower, facecolor="lightcoral", alpha=0.6)

    plt.plot(dq_median, label="Double DQN", color="navy")
    plt.fill_between(x, dq_upper, dq_median, facecolor="lightsteelblue", alpha=0.6)
    plt.fill_between(x, dq_median, dq_lower, facecolor="lightsteelblue", alpha=0.6)

    # If the true values are given, plot them as a straight line
    if true_q is not None:
        plt.axhline(true_q, label="True DQN value", color="firebrick", linestyle='dashed', alpha=0.8)
    if true_dq is not None:
        plt.axhline(true_dq, label="True Double DQN value", color="lightsteelblue", linestyle='dashed', alpha=0.8)

    # Emphasize significant values if given
    if significant_values is not None:
        num_points = q_data.shape[0] * q_data.shape[1]
        lowest_data_point = np.min([np.min(q_data.reshape(num_points)), np.min(dq_data.reshape(num_points))])
        lowest_data_point = int(lowest_data_point) - 5 if lowest_data_point != 0 else -10
        plt.scatter(
            significant_values, np.ones(significant_values.shape) * lowest_data_point,
            marker="|", color="black"
        )

    # Emphasize significant values if given
    if significant_values is not None:
        plt.scatter(significant_values, np.zeros(significant_values.shape), marker="", color="black", alpha=0.7)

    if title is not None:
        plt.title(title)

    plt.legend(fontsize=8)
    plt.tight_layout()
    plt.savefig(file_name)
    plt.close()


def plot_data_for_env(env_name, q_data, dq_data, image_path):
    q_values, q_rewards, q_durations, true_q = q_data["values"], q_data["rewards"], q_data["durations"], q_data["true"]
    dq_values, dq_rewards, dq_durations, true_dq = dq_data["values"], dq_data["rewards"], dq_data["durations"], dq_data["true"]

    # Do significance-testing
    print(env_name)
    print("Q-values")
    _, significant_scores = test_difference(q_values, dq_values)
    print("Rewards")
    _, significant_rewards = test_difference(q_rewards, dq_rewards)
    print("Durations")
    _, significant_durations = test_difference(q_durations, dq_durations)
    print("")

    plot_exps_with_intervals(
        q_values, dq_values, title=f"{env_name} Q-Values", file_name=f"{image_path}/qvalues_{env_name.lower()}.png",
        smooth_curves=False, true_q=true_q, true_dq=true_dq, significant_values=significant_scores
    )

    plot_exps_with_intervals(
        q_rewards, dq_rewards, title=f"{env_name} Rewards", file_name=f"{image_path}/rewards_{env_name.lower()}.png",
        smooth_curves=False, significant_values=significant_rewards
    )

    plot_exps_with_intervals(
        q_durations, dq_durations, title=f"{env_name} Durations", file_name=f"{image_path}/durations_{env_name.lower()}.png",
        smooth_curves=False, significant_values=significant_durations
    )
