from scipy.stats import binom, norm
import numpy as np
from scipy.stats import binom, norm
import numpy as np

def bayesian_3pt_percentage_with_credible_interval(historical_pct, current_attempts, current_made, prior_std=0.1, credible_level=0.95):

    #Prior Distribution
    prior_distribution = norm(historical_pct, prior_std)

    #Likelihood Function
    likelihood = binom(current_attempts, current_made/current_attempts)

    #Update the Prior with Current Data (Posterior Distribution)
    percentage_values = np.linspace(0, 1, 1000)  # Possible 3-point percentages
    posterior_probabilities = likelihood.pmf(current_made) * prior_distribution.pdf(percentage_values)

    # Check if the sum of posterior probabilities is very small or zero
    sum_posterior = np.sum(posterior_probabilities)
    if sum_posterior < 1e-8:
        raise ValueError("Sum of posterior probabilities is too small, check your prior_std or data.")

    # Normalize the posterior probabilities
    posterior_probabilities /= sum_posterior

    # Calculate the Bayesian 3-Point Percentage
    bayesian_estimate = np.sum(percentage_values * posterior_probabilities)

    # Calculate the credible interval
    cumulative_probabilities = np.cumsum(posterior_probabilities)
    lower_bound_idx = np.where(cumulative_probabilities >= (1 - credible_level) / 2)[0][0]
    upper_bound_idx = np.where(cumulative_probabilities >= 1 - (1 - credible_level) / 2)[0][0]

    return bayesian_estimate, percentage_values[lower_bound_idx], percentage_values[upper_bound_idx]
