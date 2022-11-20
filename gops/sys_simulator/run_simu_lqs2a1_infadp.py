from sys_run import PolicyRunner

runner = PolicyRunner(
    log_policy_dir_list=["./results/INFADP/simu_lqs2a1"]*2,
    trained_policy_iteration_list=['10000', '9500'],
    is_init_info=True,
    init_info={"init_state":[0.5, -0.5]},
    save_render=False,
    legend_list=['INFADP-10000', 'INFADP-95000'],
    use_opt=True)

runner.run()