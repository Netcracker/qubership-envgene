from pipeline_parameters import PipelineParametersHandler, log_pipeline_params

if __name__ == '__main__':
    handler = PipelineParametersHandler()
    params = handler.params.copy()
    log_pipeline_params(params)