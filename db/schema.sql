-- Authoritative read-only analytics schema for GChSPFAM-GE-3RF.
-- Apply with an administrative Neon connection. The public app uses a separate
-- read-only role; see readonly_role.sql.example.

create schema if not exists research;

create table if not exists research.import_manifest (
    dataset text not null,
    source_file text not null,
    sha256 text not null,
    source_rows bigint not null check (source_rows >= 0),
    imported_rows bigint not null check (imported_rows >= 0),
    status text not null check (status in ('running', 'complete', 'failed')),
    imported_at timestamptz not null default now(),
    primary key (dataset, source_file)
);

-- Candidate metadata is constant across g=1,...,500 for each prior-scenario
-- combination. Store it once to keep the complete experiment within a
-- practical PostgreSQL footprint while retaining double precision.
create table if not exists research.analysis_units (
    analysis_unit_id bigint generated always as identity primary key,
    scenario_id text not null,
    prior_id text not null,
    prior_mean double precision not null,
    prior_sd double precision not null,
    beta_alpha double precision not null,
    beta_beta double precision not null,
    acceptable_mean_life_ratio double precision not null,
    termination_multiplier double precision not null,
    ge_shape double precision not null,
    group_size_r bigint not null,
    chain_parameter_i bigint not null,
    p1 double precision not null,
    p2 double precision not null,
    prior_good_probability double precision not null,
    prior_bad_probability double precision not null,
    unique (scenario_id, prior_id)
);

create table if not exists research.candidate_fact (
    analysis_unit_id bigint not null references research.analysis_units (analysis_unit_id),
    candidate_g smallint not null check (candidate_g between 1 and 500),
    candidate_n integer not null,
    pr double precision not null,
    apr double precision not null,
    bpr double precision not null,
    cr double precision not null,
    acr double precision not null,
    bcr double precision not null,
    msr double precision not null,
    msar double precision not null,
    msbr double precision not null,
    l_p1 double precision not null,
    l_p2 double precision not null,
    classical_feasible boolean not null,
    average_feasible boolean not null,
    bayesian_feasible boolean not null,
    source_part text not null,
    primary key (analysis_unit_id, candidate_g)
);

-- Preserve the authoritative 31-column candidate dataset contract for the
-- application and validation queries. This view contains all 2,592,000 rows.
create or replace view research.candidate_results as
select
    u.scenario_id,
    u.prior_id,
    u.prior_mean,
    u.prior_sd,
    u.beta_alpha,
    u.beta_beta,
    u.acceptable_mean_life_ratio,
    u.termination_multiplier,
    u.ge_shape,
    u.group_size_r,
    u.chain_parameter_i,
    u.p1,
    u.p2,
    f.candidate_g,
    f.candidate_n,
    f.pr,
    f.apr,
    f.bpr,
    f.cr,
    f.acr,
    f.bcr,
    f.msr,
    f.msar,
    f.msbr,
    f.l_p1,
    f.l_p2,
    u.prior_good_probability,
    u.prior_bad_probability,
    f.classical_feasible,
    f.average_feasible,
    f.bayesian_feasible
from research.candidate_fact f
join research.analysis_units u using (analysis_unit_id);

create table if not exists research.selected_plans (
    scenario_id text not null,
    prior_id text not null,
    prior_mean double precision not null,
    prior_sd double precision not null,
    beta_alpha double precision not null,
    beta_beta double precision not null,
    acceptable_mean_life_ratio double precision not null,
    termination_multiplier double precision not null,
    ge_shape double precision not null,
    group_size_r bigint not null,
    chain_parameter_i bigint not null,
    p1 double precision not null,
    p2 double precision not null,
    framework text not null check (framework in ('Classical', 'Average', 'Bayesian')),
    consumer_risk_limit double precision not null,
    feasible boolean not null,
    selected_g bigint,
    selected_n bigint,
    pr double precision,
    apr double precision,
    bpr double precision,
    cr double precision,
    acr double precision,
    bcr double precision,
    msr double precision,
    msar double precision,
    msbr double precision,
    l_p1 double precision,
    l_p2 double precision,
    framework_producer_risk double precision,
    framework_consumer_risk double precision,
    framework_risk_sum double precision,
    consumer_risk_margin double precision,
    numerical_validation_status text,
    primary key (scenario_id, prior_id, framework)
);

create table if not exists research.matched_framework_results (
    scenario_id text not null,
    prior_id text not null,
    prior_mean double precision not null,
    prior_sd double precision not null,
    beta_alpha double precision not null,
    beta_beta double precision not null,
    acceptable_mean_life_ratio double precision not null,
    termination_multiplier double precision not null,
    ge_shape double precision not null,
    group_size_r bigint not null,
    chain_parameter_i bigint not null,
    p1 double precision not null,
    p2 double precision not null,
    consumer_risk_limit double precision not null,
    classical_feasible boolean not null,
    classical_selected_g bigint,
    classical_selected_n bigint,
    classical_pr double precision, classical_apr double precision, classical_bpr double precision,
    classical_cr double precision, classical_acr double precision, classical_bcr double precision,
    classical_msr double precision, classical_msar double precision, classical_msbr double precision,
    classical_l_p1 double precision, classical_l_p2 double precision,
    classical_framework_producer_risk double precision,
    classical_framework_consumer_risk double precision,
    classical_framework_risk_sum double precision,
    classical_consumer_risk_margin double precision,
    classical_numerical_validation_status text,
    average_feasible boolean not null,
    average_selected_g bigint,
    average_selected_n bigint,
    average_pr double precision, average_apr double precision, average_bpr double precision,
    average_cr double precision, average_acr double precision, average_bcr double precision,
    average_msr double precision, average_msar double precision, average_msbr double precision,
    average_l_p1 double precision, average_l_p2 double precision,
    average_framework_producer_risk double precision,
    average_framework_consumer_risk double precision,
    average_framework_risk_sum double precision,
    average_consumer_risk_margin double precision,
    average_numerical_validation_status text,
    bayesian_feasible boolean not null,
    bayesian_selected_g bigint,
    bayesian_selected_n bigint,
    bayesian_pr double precision, bayesian_apr double precision, bayesian_bpr double precision,
    bayesian_cr double precision, bayesian_acr double precision, bayesian_bcr double precision,
    bayesian_msr double precision, bayesian_msar double precision, bayesian_msbr double precision,
    bayesian_l_p1 double precision, bayesian_l_p2 double precision,
    bayesian_framework_producer_risk double precision,
    bayesian_framework_consumer_risk double precision,
    bayesian_framework_risk_sum double precision,
    bayesian_consumer_risk_margin double precision,
    bayesian_numerical_validation_status text,
    primary key (scenario_id, prior_id)
);

create table if not exists research.fixed_plan_oc (
    fixed_plan_id text not null,
    prior_id text not null,
    prior_mean double precision not null,
    prior_sd double precision not null,
    beta_alpha double precision not null,
    beta_beta double precision not null,
    ge_shape double precision not null,
    termination_multiplier double precision not null,
    group_size_r bigint not null,
    chain_parameter_i bigint not null,
    framework text not null check (framework in ('Classical', 'Average', 'Bayesian')),
    selected_g bigint not null,
    selected_n bigint not null,
    consumer_risk_limit double precision not null,
    feasible boolean not null,
    evaluation_mean_life_ratio double precision not null,
    failure_probability_p double precision not null,
    l_p double precision not null,
    design_ratio_invariance_verified boolean not null,
    primary key (fixed_plan_id, evaluation_mean_life_ratio)
);

create table if not exists research.validation_summary (
    name text primary key,
    payload jsonb not null,
    imported_at timestamptz not null default now()
);

create index if not exists ix_candidate_fact_source_part on research.candidate_fact (source_part);
create index if not exists ix_selected_filters on research.selected_plans
    (framework, ge_shape, termination_multiplier, acceptable_mean_life_ratio, prior_id);
create index if not exists ix_fixed_oc_filters on research.fixed_plan_oc
    (prior_id, ge_shape, termination_multiplier, group_size_r, chain_parameter_i, framework);

