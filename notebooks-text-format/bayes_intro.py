# -*- coding: utf-8 -*-
# ---
# jupyter:
#   jupytext:
#     text_representation:
#       extension: .py
#       format_name: light
#       format_version: '1.5'
#       jupytext_version: 1.11.3
#   kernelspec:
#     display_name: Python 3
#     language: python
#     name: python3
# ---

# + [markdown] id="view-in-github" colab_type="text"
# <a href="https://colab.research.google.com/github/probml/pyprobml/blob/master/notebooks/bayes_intro.ipynb" target="_parent"><img src="https://colab.research.google.com/assets/colab-badge.svg" alt="Open In Colab"/></a>

# + [markdown] id="zB6ogdFJ7Liw"
# # Bayesian Statistics 
#
# In this notebook, we illustrate some basic concepts in (computaitonal) Bayesian statistics. We borrow some code examples from chapter 2 of [Bayesian Analysis with Python (2nd end)](https://github.com/aloctavodia/BAP) by Osvaldo Martin.
#
#
#

# + [markdown] id="ennfUwYYP2vF"
# * The primary goal is to infer the posterior of the parameters $\theta$ of some model given observations or data $D=(y_1,\ldots,y_n)$:
# $$
# p(\theta|D) = \frac{p(\theta) p(D|\theta)}{p(D)}
# $$
# * If we assume the observations are independently sampled and identically distributed (iid), then we can write the likelihood as
# $$
# p(D|\theta) = \prod_{n=1}^N p(y_n|\theta)
# $$
# * If we have features, we can fit a conditional or discriminative model of the form $p(y|x;\theta)$, where the model generates the output $y$ given the input $x$. In this case, the likelihood becomes 
# $$
# p(D|\theta) = \prod_{n=1}^N p(y_n|x_n;\theta)
# $$

# + id="VdDT44uy7Liz"
# %matplotlib inline
import sklearn
import scipy.stats as stats
import scipy.optimize
import matplotlib.pyplot as plt
import seaborn as sns
import time
import numpy as np
import os
import pandas as pd


# + id="v7_mOF6dqbO0" colab={"base_uri": "https://localhost:8080/"} outputId="6665c42d-9b3b-4ada-d7ce-54c777619c3e"
# We install various packages  we will need

# The PyMC3 package (https://docs.pymc.io) supports HMC and variational inference
# https://docs.pymc.io/notebooks/api_quickstart.html
#Installed version of ArviZ requires PyMC3>=3.8
# !pip install pymc3==3.8
# #!pip install pymc3>=3.8 # does not work
import pymc3 as pm
pm.__version__

# The arviz package (https://github.com/arviz-devs/arviz) can be used to make various plots
# of posterior samples generated by any algorithm. 
# !pip install arviz
import arviz as az

# + [markdown] id="MbXiE1iTuVal"
# # Beta-Binomial model
#
#

# + [markdown] id="htnJXhfp54ph"
# ## Exact inference

# + id="km5WZG3Vuvsm" colab={"base_uri": "https://localhost:8080/", "height": 528} outputId="3a960c0c-c98e-4961-8d58-291fd94aa251"
# Plot the Binomial likelihood

n_params = [1, 2, 4]  # Number of trials
p_params = [0.25, 0.5, 0.75]  # Probability of success

x = np.arange(0, max(n_params)+1)
f,ax = plt.subplots(len(n_params), len(p_params), sharex=True, sharey=True,
                    figsize=(8, 7), constrained_layout=True)

for i in range(len(n_params)):
    for j in range(len(p_params)):
        n = n_params[i]
        p = p_params[j]

        y = stats.binom(n=n, p=p).pmf(x)

        ax[i,j].vlines(x, 0, y, colors='C0', lw=5)
        ax[i,j].set_ylim(0, 1)
        ax[i,j].plot(0, 0, label="N = {:3.2f}\nθ = {:3.2f}".format(n,p), alpha=0)
        ax[i,j].legend()

        ax[2,1].set_xlabel('y')
        ax[1,0].set_ylabel('p(y | θ, N)')
        ax[0,0].set_xticks(x)


# + id="VGM_MaWrvFPh" colab={"base_uri": "https://localhost:8080/", "height": 528} outputId="7a4926c3-5f03-45b4-ee5a-15c3d4b494e5"
# Plot the beta prior

params = [0.5, 1, 2, 3]
x = np.linspace(0, 1, 100)
f, ax = plt.subplots(len(params), len(params), sharex=True, sharey=True,
                     figsize=(8, 7), constrained_layout=True)
for i in range(4):
    for j in range(4):
        a = params[i]
        b = params[j]
        y = stats.beta(a, b).pdf(x)
        ax[i,j].plot(x, y)
        ax[i,j].plot(0, 0, label="α = {:2.1f}\nβ = {:2.1f}".format(a, b), alpha=0)
        ax[i,j].legend()
ax[1,0].set_yticks([])
ax[1,0].set_xticks([0, 0.5, 1])
f.text(0.5, 0.05, 'θ', ha='center')
f.text(0.07, 0.5, 'p(θ)', va='center', rotation=0)


# + id="KRzPSd0cvP3p" colab={"base_uri": "https://localhost:8080/", "height": 584} outputId="95363d81-07b9-4ab6-ecb2-191d00602def"
# Compute and plot posterior (black vertical line = true parameter value)

plt.figure(figsize=(10, 8))

n_trials = [0, 1, 2, 3, 4, 8, 16, 32, 50, 150]
data = [0, 1, 1, 1, 1, 4, 6, 9, 13, 48]
theta_real = 0.35

beta_params = [(1, 1), (20, 20), (1, 4)]
dist = stats.beta
x = np.linspace(0, 1, 200)

for idx, N in enumerate(n_trials):
    if idx == 0:
        plt.subplot(4, 3, 2)
        plt.xlabel('θ')
    else:
        plt.subplot(4, 3, idx+3)
        plt.xticks([])
    y = data[idx]
    for (a_prior, b_prior) in beta_params:
        p_theta_given_y = dist.pdf(x, a_prior + y, b_prior + N - y)
        plt.fill_between(x, 0, p_theta_given_y, alpha=0.7)

    plt.axvline(theta_real, ymax=0.3, color='k')
    plt.plot(0, 0, label=f'{N:4d} trials\n{y:4d} heads', alpha=0)
    plt.xlim(0, 1)
    plt.ylim(0, 12)
    plt.legend()
    plt.yticks([])
plt.tight_layout()


# + [markdown] id="TjGukFgD7Li2"
# ## Credible intervals <a class="anchor" id="credible"></a>
#
#
#

# + id="RPVLjF_-7Li3" colab={"base_uri": "https://localhost:8080/", "height": 87} outputId="4f8cb00a-9a98-4be3-f374-3e7fd99b0e5c"
# We illustrate how to compute a 95% posterior credible interval for a random variable
# with a beta distribution.

from scipy.stats import beta

np.random.seed(42)
theta_real = 0.35
ntrials = 100
data = stats.bernoulli.rvs(p=theta_real, size=ntrials)

N = ntrials; N1 = sum(data); N0 = N-N1; # Sufficient statistics
aprior = 1; bprior = 1; # prior
apost = aprior + N1; bpost = bprior + N0 # posterior

# Interval function
alpha = 0.05
CI1 = beta.interval(1-alpha, apost, bpost)
print('{:0.2f}--{:0.2f}'.format(CI1[0], CI1[1])) # (0.06:0.52) 

# Use the inverse CDF (percent point function)
l  = beta.ppf(alpha/2, apost, bpost)
u  = beta.ppf(1-alpha/2, apost, bpost)
CI2 = (l,u)
print('{:0.2f}--{:0.2f}'.format(CI2[0], CI2[1])) # (0.06:0.52) 

# Use Monte Carlo sampling
samples = beta.rvs(apost, bpost, size=10000)
samples = np.sort(samples)
CI3 = np.percentile(samples, 100*np.array([alpha/2, 1-alpha/2])) 
print('{:0.2f}--{:0.2f}'.format(CI3[0], CI3[1])) # (0.06:0.51) 
print(np.mean(samples))


# + id="OxwrDdco7Li6" colab={"base_uri": "https://localhost:8080/", "height": 313} outputId="41b537cc-19e6-4322-eba6-c0b6bb4ddcc8"
# Use arviz to plot posterior.
# By default, it shows the 94\% interval, but we change it to 95%.

az.plot_posterior({'θ':samples}, credible_interval=0.95);

# + id="LzQnCl6ULXHr" colab={"base_uri": "https://localhost:8080/", "height": 348} outputId="b7758aaa-3c92-48f4-fc8e-2810edac5340"
# See if the parameter is inside the region of practical equivalence centered at 0.5
az.plot_posterior(samples, rope=[0.45, .55]);

# + id="2jDIS28ELmC2" colab={"base_uri": "https://localhost:8080/", "height": 313} outputId="6d1d5f42-809a-4872-93ac-4eb96b823225"
# From the above plot, we see that the HPD does not overlap the ROPE,
#so we can confidently say the parameter is "significiantly different" from 0.5

# We can also verify this by checking if 0.5 is in the HPD
az.plot_posterior(samples,  credible_interval=0.95, ref_val=0.5);

# + id="l8u13QAtm4K6" colab={"base_uri": "https://localhost:8080/", "height": 95} outputId="c64bd156-538e-4c2d-d7d0-1c243fe7e700"
# Summarize  posterior samples
az.summary(samples)
# We can ignore the warning about not having enough 'chains',
# since we are drawing exact iid samples from the posterior.

# + [markdown] id="UVJ671UrMyBU"
# ## Point estimates
#
# We minimize the posterior expected loss, using L2 loss (estimator is posterior mean) or L1 loss (estimator is posterior median).

# + id="ObD6JjyHM-nF" colab={"base_uri": "https://localhost:8080/", "height": 285} outputId="14c89acb-6510-44b2-d942-3186013bf4d7"
grid = np.linspace(0, 1, 200)
θ_pos = samples #trace['θ']
lossf_a = [np.mean(abs(i - θ_pos)) for i in grid]
lossf_b = [np.mean((i - θ_pos)**2) for i in grid]

for lossf, c in zip([lossf_a, lossf_b], ['C0', 'C1']):
    mini = np.argmin(lossf)
    plt.plot(grid, lossf, c)
    plt.plot(grid[mini], lossf[mini], 'o', color=c)
    plt.annotate('{:.3f}'.format(grid[mini]),
                 (grid[mini], lossf[mini] + 0.03), color=c)
    plt.yticks([])
    plt.xlabel(r'$\hat \theta$')

# + [markdown] id="OTbNQWS5GlrZ"
# ## MCMC inference 
#
# We will use pymc3 to approximate the posterior of this simple model.
# Code is based on [this notebook](https://github.com/aloctavodia/BAP/blob/master/code/Chp202%20Programming%20probabilistically.ipynb).
#
#

# + id="VBkitXPNDas8" colab={"base_uri": "https://localhost:8080/", "height": 105} outputId="24aed058-b8d0-46b1-b1b8-43e88045c37f"
data # same as above

# + id="mOxQ28fcTfq4" colab={"base_uri": "https://localhost:8080/", "height": 226} outputId="f2df35ea-0c8f-4c74-d43c-a52d8fee3889"
with pm.Model() as model:
    # a priori
    θ = pm.Beta('θ', alpha=aprior, beta=bprior)
    # likelihood
    y = pm.Bernoulli('y', p=θ, observed=data)

pm.model_to_graphviz(model) # show the DAG

# + id="4geCJWUmG6pN" colab={"base_uri": "https://localhost:8080/", "height": 123} outputId="74d0044b-06d4-4c41-9024-9e73f195055f"
# run MCMC (defaults to 2 chains)
with model:
    trace = pm.sample(1000, random_seed=123)

# + id="q6swy2ktjz1j" colab={"base_uri": "https://localhost:8080/", "height": 240} outputId="73e71056-8c5b-48c5-9592-05e21524e920"
 # Standard MCMC diagonistics
pm.traceplot(trace);
Rhat = pm.rhat(trace);
print(Rhat) # should be close to 1.0


# + id="H_rLxDAalo1I" colab={"base_uri": "https://localhost:8080/", "height": 313} outputId="5c0bea60-3eb2-41c4-c9c8-3f7bfa5239fc"
pm.plot_posterior(trace);
# The samples from MCMC (called "trace") should be similar to the exact
# iid samples from the posterior, plotted above
# Under the hood, pm.plot_posterior(trace) calls az.plot_posterior(trace)

# + id="p0LjS8i6Hh3L" colab={"base_uri": "https://localhost:8080/", "height": 77} outputId="58615a63-8d08-4771-9617-22e8402b5c36"
# Summarize  posterior samples
pm.summary(trace)


# + id="Wphw6LxtYTJa" colab={"base_uri": "https://localhost:8080/", "height": 313} outputId="7c29f5cb-1ba6-4122-b557-4ce300523191"
# Convert posterior samples into a parametric distribution
trace_approx = pm.Empirical(trace, model=model)
# Now plot samples from this distribution
az.plot_posterior(trace_approx.sample(1000));

# + [markdown] id="XAIHT4ylWjfE"
# ## Variational inference 
#
# We use automatic differentiation VI.
# Details can be found at https://docs.pymc.io/notebooks/variational_api_quickstart.html

# + id="CuOl7b8DQy9F" colab={"base_uri": "https://localhost:8080/", "height": 52} outputId="94eaf115-eba3-4ee2-a501-efc797e0b6e1"
niter = 10000
with model:
    post = pm.fit(niter, method='advi'); # mean field approximation


# + id="k8sDAOU5W3el" colab={"base_uri": "https://localhost:8080/", "height": 264} outputId="8cf91e70-a676-4ca7-dcc9-234d12f7264d"
# Plot negative ELBO vs iteration to assess convergence
plt.plot(post.hist);

# + id="Lqbq0ufEVve6" colab={"base_uri": "https://localhost:8080/", "height": 313} outputId="7149d022-85df-4b34-8ae3-9b407d7deee9"
pm.plot_posterior(post.sample(1000));

# + [markdown] id="cJMTdmeFxl1r"
# # 1d Gaussian 

# + [markdown] id="WXafZ91X6K7S"
# ## Exact inference
#
# For simplicity, we assume the variance is known, and we just want to infer the mean.

# + id="OUtJiE__PPnr" colab={"base_uri": "https://localhost:8080/", "height": 34} outputId="2db3fc74-8601-4a2b-9390-4797d1223518"
np.random.seed(0)
N = 100
x = np.random.randn(100)

# Parameters of prior
mu_prior = 1.1
sigma_prior = 1.2 #std
Sigma_prior = sigma_prior**2 #var

# Parameters of likelihood
sigma_x = 1.3
Sigma_x = sigma_x**2

# Bayes rule for Gaussians 
Sigma_post = 1/( 1/Sigma_prior + N/Sigma_x )
xbar = np.mean(x)
mu_post = Sigma_post * (1/Sigma_x * N * xbar + 1/Sigma_prior * mu_prior);
print('p(mu|D)=N(mu|{:.3f}, {:.3f})'.format(mu_post, Sigma_post))


# + [markdown] id="gML2sLLm6HO4"
# ## MCMC inference

# + [markdown] id="5oRpTekEQB-N"
# Initially we assume the variance is known, so we can compare results to exact infernece.

# + id="Fc9pWH5mPp4K" colab={"base_uri": "https://localhost:8080/", "height": 457} outputId="b61ae67e-2896-4e82-bd33-5105ac03d13e"
with pm.Model() as model:
    mu = pm.Normal('mu', mu=mu_prior, sd=sigma_prior)
    obs = pm.Normal('obs', mu=mu, sd=sigma_x, observed=x)
    mcmc_samples = pm.sample(1000, tune=500) # mcmc
    
pm.plot_posterior(mcmc_samples);


# + id="iPNspmtyoiDa" colab={"base_uri": "https://localhost:8080/", "height": 34} outputId="ae425d96-afb5-4834-f335-70ece83b7107"
vals = mcmc_samples.get_values('mu')
mu_post_mcmc = np.mean(vals)
Sigma_post_mcmc = np.var(vals)
print('pMCMC(mu|D)=N(mu|{:.3f}, {:.3f})'.format(mu_post_mcmc, Sigma_post_mcmc))
assert np.isclose(mu_post, mu_post_mcmc, atol=1e-1)
assert np.isclose(Sigma_post, Sigma_post_mcmc, atol=1e-1)

# + id="kpJ689WVpbBj"
# We can also evaluate the log joint at any given point in parameter space.
# The 'obs' variable is already observed (value=x)
# so the only unknown is mu. Let's clamp it to some value
# and compute log p(mu, D)
mu_clamped = -0.5    
logp = model.logp({'mu': mu_clamped})

# Computed the log joint "by hand"
log_prior = scipy.stats.norm(mu_prior, sigma_prior).logpdf(mu_clamped)
log_lik  = np.sum(scipy.stats.norm(mu_clamped, sigma_x).logpdf(x))
log_joint = log_prior + log_lik

assert np.isclose(logp, log_joint)


# + [markdown] id="RAgqwp_yQGZ7"
# Now we consider the case where the mean and variance are both unknown.
# We also switch to a "real world" dataset, of "chemical shifts", that has a couple of "outliers".

# + id="2JsH9w0Avrws" colab={"base_uri": "https://localhost:8080/", "height": 105} outputId="6fafe52c-f683-42aa-d524-4065d73d2382"

#url = 'https://github.com/aloctavodia/BAP/blob/master/code/data/chemical_shifts.csv'
url = 'https://raw.githubusercontent.com/aloctavodia/BAP/master/code/data/chemical_shifts.csv'

df = pd.read_csv(url)
# b=df.iloc[:,1:].values
#data = df.to_numpy() 
data = df.iloc[:,0].values
print(data.shape)
print(data)

# + id="YrXia9R6wjaq" colab={"base_uri": "https://localhost:8080/", "height": 304} outputId="44072d6f-f2ea-4d53-8a11-803cca5c33cc"
az.plot_kde(data, rug=True)
plt.yticks([0], alpha=0)

# + id="9Rn0gpeNxsyN" colab={"base_uri": "https://localhost:8080/", "height": 244} outputId="87b13dd0-665e-4626-8eb9-0e49217bc0d4"
# We will infer a posterior for the mean and variance.
# We use a uniform prior for the mean, with support slightly larger than the data.
# We use a truncated normal for the variance, with effective support uniform 0 to 3*std.
r = np.max(data)-np.min(data)
min_mu = np.min(data)-0.1*r
max_mu = np.max(data)+0.1*r
prior_std = 3*np.std(data)
print([min_mu, max_mu, prior_std])

with pm.Model() as model_g:
    μ = pm.Uniform('μ', lower=min_mu, upper=max_mu)
    σ = pm.HalfNormal('σ', sd=10)
    y = pm.Normal('y', mu=μ, sd=σ, observed=data)

pm.model_to_graphviz(model_g) # show the DAG


# + id="LkC9vsZpyu73" colab={"base_uri": "https://localhost:8080/", "height": 123} outputId="6974e5ac-0a2a-4429-e143-76470855d0fc"
with model_g:
    trace_g = pm.sample(1000, random_seed=123)

# + id="hox02Yx-z4u8" colab={"base_uri": "https://localhost:8080/", "height": 313} outputId="c359220c-dcba-4136-c34f-b4f4a03786ca"
az.plot_trace(trace_g);

# + id="fZA-TErnzwVa" colab={"base_uri": "https://localhost:8080/", "height": 107} outputId="f24f719c-8566-4837-c2f9-415412ac7f5d"
az.summary(trace_g)

# + id="rUtXM1umzytN" colab={"base_uri": "https://localhost:8080/", "height": 313} outputId="9925026c-622c-422e-c483-9ac83824fa92"
az.plot_joint(trace_g, kind='kde', fill_last=False);

# + [markdown] id="b9kj8t0H0RKA"
# ## Posterior predictive checks

# + id="NHFGfDyO0QCH" colab={"base_uri": "https://localhost:8080/", "height": 143} outputId="99f65cf6-f7e9-4f7c-b651-357a589764d8"
# We check how well the gaussian assumption fits our data
# by sampling from the fitted model, and plotting the samples
# and the original data.
# For details, see https://docs.pymc.io/notebooks/posterior_predictive.html

# For the Gaussian model, the mean and variance is higher than for the observed data, 
# indicating poor fit.
y_pred_g = pm.sample_posterior_predictive(trace_g, 100, model_g)

print(y_pred_g.keys())
v=y_pred_g['y']
print(type(v))
print(v.shape) # 100 x 47






# + id="TMnXnmEy0aE7" colab={"base_uri": "https://localhost:8080/", "height": 512} outputId="13dc4136-5711-41da-d51a-680f900f6810"
data_ppc = az.from_pymc3(trace=trace_g, posterior_predictive=y_pred_g)
ax = az.plot_ppc(data_ppc, figsize=(12, 6), mean=False);
ax[0].legend(fontsize=15)

# + [markdown] id="OVrJn2494xv4"
# ## Robust likelihood (1d Student distribution)

# + id="IPLghoxx0cHG" colab={"base_uri": "https://localhost:8080/", "height": 684} outputId="eec57470-4f3b-4e37-86cc-279afaa7a42e"
# We replace the above Gaussian likelihood with a Student t distribution.
# The degree of freedom parameter \nu > 0 (also called the "normality parameter")
# determines how close to Normal the distribution is.
# nu=1 corredsponds to a Cauchy, nu >> 10 corresponds to a Gaussian.
# We put an Exponential prior on nu, with a mean of 30.

with pm.Model() as model_t:
    μ = pm.Uniform('μ', 40, 75)
    σ = pm.HalfNormal('σ', sd=10)
    ν = pm.Exponential('ν', 1/30) # PyMC3 uses inverse of the mean
    y = pm.StudentT('y', mu=μ, sd=σ, nu=ν, observed=data)

pm.model_to_graphviz(model_t) # show the DAG

with model_t:
    trace_t = pm.sample(1000)

az.plot_trace(trace_t)

az.summary(trace_t)
# We see that E[nu]=4.5, which is fairly far from Gaussian
# We see E[sigma]=2.1, wich is less than the 3.5 estimate from Gaussian likelihood


# + id="SmtwtKhL5py7" colab={"base_uri": "https://localhost:8080/", "height": 565} outputId="844bd615-67aa-4e06-a6c6-abc41e8d71c1"
# posterior predictive check

y_ppc_t = pm.sample_posterior_predictive(
    trace_t, 100, model_t, random_seed=123)
y_pred_t = az.from_pymc3(trace=trace_t, posterior_predictive=y_ppc_t)
az.plot_ppc(y_pred_t, figsize=(12, 6), mean=False)
ax[0].legend(fontsize=15)
plt.xlim(40, 70)


# + id="vGpg-hpX6lmG" colab={"base_uri": "https://localhost:8080/", "height": 52} outputId="0b4d20ce-3945-4d88-95ae-22e340c24b1a"
# Remove outliers from data and compare empirical mean and variance of cleaned data
# to posterior mean and posterior scale of a Student likelihood

# https://gist.github.com/vishalkuo/f4aec300cf6252ed28d3
def removeOutliers(x, outlierConstant=1.5):
    a = np.array(x)
    upper_quartile = np.percentile(a, 75)
    lower_quartile = np.percentile(a, 25)
    IQR = (upper_quartile - lower_quartile) * outlierConstant
    quartileSet = (lower_quartile - IQR, upper_quartile + IQR)
    result = a[np.where((a >= quartileSet[0]) & (a <= quartileSet[1]))]
    return result.tolist()

data_clean = removeOutliers(data)
mu_mcmc = np.mean(trace_t.get_values('μ'))
sigma_mcmc = np.mean(trace_t.get_values('σ'))

print([np.mean(data), np.mean(data_clean), mu_mcmc])
print([np.std(data), np.std(data_clean), sigma_mcmc])


# + [markdown] id="RxKiMs32-i9m"
# # Comparing means of different datasets
#
# We often want to know if one dataset, $D_i$,  has a "statistically signficant" difference in one of its parameters, such as its mean $\mu_i$, compared to some other dataset, $D_j$. We can answer this in a Bayesian way by computing $p(\delta_{ij}|D_i,D_j)$, where
#
# $\delta_{ij}=\mu_i-\mu_j$.
#
# To do this, we draw samples from $p(\mu_i|D_i)$ and $p(\mu_j|D_j)$.
#
# Since the magnitude of $\delta_{ij}$ can be hard to interpret, it is common to divide it by the pooled standard deviation, to get a metric known as Cohen's d (see [this website](https://rpsychologist.com/d3/cohend/) for details):
#
# $d_{ij} = \frac{\mu_j - \mu_i}{\sqrt{\frac{\sigma_i^2 + \sigma_j^2}{2}}}$
#
# We can compute $p(d_{ij}|D_i,D_j)$ using posterior samples of $\mu_i,\mu_j,\sigma_i,\sigma_j$.
#
#
#
#
#
#
#

# + id="6sizlMD2700t" colab={"base_uri": "https://localhost:8080/", "height": 191} outputId="17d6289a-0ff4-4b39-92e2-2b7478a45c52"
#We illustrate this below using the same dataset as used in chap 2 of
#["Bayesian Analysis with Python (2nd end)"](https://github.com/aloctavodia/BAP) that records how much tips waiters made.

url = 'https://raw.githubusercontent.com/aloctavodia/BAP/master/code/data/tips.csv'
df = pd.read_csv(url)
df.tail()

# + id="jAiEPSrgASik" colab={"base_uri": "https://localhost:8080/", "height": 295} outputId="ddd55ad0-f491-41b0-96d4-07460998a170"
# We look at the effect of day on tip amount.
# We ignore other covariates, such as gender.

sns.violinplot(x='day', y='tip', data=df)


# + id="RgQO3kcPB73t" colab={"base_uri": "https://localhost:8080/"} outputId="d3f85ab2-2631-4010-b1eb-cf3f4f565605"
# We will compute 4 groups, corresponding to Thur-Sun.
x=df['day'].values
print(type(x))
print(x)
print(np.unique(x))

# + id="gULAsE35CAzc" colab={"base_uri": "https://localhost:8080/"} outputId="da7ddddf-df68-4348-b3d8-4453af65dfe0"
tip_amount = df['tip'].values
days = ['Thur', 'Fri', 'Sat', 'Sun']
#idx = pd.Categorical(tips['day'], categories=days).codes
idx = pd.Categorical(df['day'], categories=days).codes 
ngroups = len(np.unique(idx))
print(idx)

# + id="BPVWDYviCVM6" colab={"base_uri": "https://localhost:8080/", "height": 1000} outputId="cbff28ad-6a3a-445c-c51c-379d6575a524"
with pm.Model() as model_cg:
    μ = pm.Normal('μ', mu=0, sd=10, shape=ngroups)
    σ = pm.HalfNormal('σ', sd=10, shape=ngroups)
    y = pm.Normal('y', mu=μ[idx], sd=σ[idx], observed=tip_amount)

print(model_cg.basic_RVs)

with model_cg:
    trace_cg = pm.sample(5000)

az.plot_trace(trace_cg)
az.summary(trace_cg)

# + id="2PcXjR8yCuLo" colab={"base_uri": "https://localhost:8080/", "height": 601} outputId="e7504f94-a16e-4fd0-ce14-7890c8652dc5"
# Looking at the posterior mean for the mu_i,
# we see Thur ~ Fri < Sat < Sun.
# But to see if these differences are significant, we should take
# into account the variability. We illustrate this below.
# We see that Thursday and Friday both earn significantly less than Sunday.
# (The threshold of 0 is outside the 95% HPD).
# Other differences are less significant.

fig, ax = plt.subplots(3, 2, figsize=(14, 8), constrained_layout=True)

comparisons = [(i, j) for i in range(ngroups) for j in range(i+1, ngroups)]
pos = [(k, l) for k in range(ngroups-1) for l in (0, 1)] # position of plot

for (i, j), (k, l) in zip(comparisons, pos):
    means_diff = trace_cg['μ'][:, i] - trace_cg['μ'][:, j]
    d_cohen = (means_diff / np.sqrt((trace_cg['σ'][:, i]**2 + trace_cg['σ'][:, j]**2) / 2)).mean()
    az.plot_posterior(means_diff, ref_val=0, ax=ax[k, l],  credible_interval=0.95)
    name_i = days[i]
    name_j = days[j]
    str = 'mean {} -  mean {}'.format(name_i, name_j)
    ax[k, l].set_title(str)
    ax[k, l].plot(0, label=f"Cohen's d = {d_cohen:.2f}")
    ax[k, l].legend()


# + id="d6qj2UD7DUys"

