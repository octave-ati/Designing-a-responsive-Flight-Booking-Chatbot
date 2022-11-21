import logging
import config
import time
from datetime import datetime
from opencensus.ext.azure.log_exporter import AzureLogHandler
from opencensus.ext.azure import metrics_exporter
from opencensus.stats import aggregation as aggregation_module
from opencensus.stats import measure as measure_module
from opencensus.stats import stats as stats_module
from opencensus.stats import view as view_module
from opencensus.tags import tag_map as tag_map_module

def configure_logger():
	logger = logging.getLogger(__name__)

	logger.addHandler(AzureLogHandler(
	    connection_string=config.insights_connection_string)
	)
	return logger

def load_insights_views():

	stats = stats_module.stats
	view_manager = stats.view_manager
	stats_recorder = stats.stats_recorder

	errors_measure = measure_module.MeasureInt("number_errors",
	                                           "Number of wrongly detected information",
	                                           "1")
	sucess_measure = measure_module.MeasureInt("number_success",
	                                           "Number of successfully detected information",
	                                           "1")

	user_score = measure_module.MeasureInt("user_score",
										   "Score provided by the user at the end of each discussion",
										   "1")

	accuracy_measure = measure_module.MeasureInt("total_accuracy",
	                                           "Overall Bot Accuracy",
	                                           "%")
	errors_view = view_module.View("number_errors",
	                               "Count of the number of wrongly detected information",
	                               [],
	                               errors_measure,
	                               aggregation_module.CountAggregation())

	success_view = view_module.View("number_success",
	                               "Count of the number of successfully detected information",
	                               [],
	                               success_measure,
	                               aggregation_module.CountAggregation())

	score_view = view_module.View("user_score",
	                               "Average User Score provided by the user at the end of each discussion",
	                               [],
	                               score_measure,
	                               aggregation_module.LastValueAggregation())


	accuracy_view = view_module.View("total_accuracy",
	                               "Overall Bot Accuracy",
	                               [],
	                               accuracy_measure,
	                               aggregation_module.LastValueAggregation())


	view_manager.register_view(errors_view)
	view_manager.register_view(success_view)
	view_manager.register_view(score_view)
	view_manager.register_view(accuracy_view)

	mmap = stats_recorder.new_measurement_map()
	tmap = tag_map_module.TagMap()

	exporter = metrics_exporter.new_metrics_exporter(
		enable_standard_metrice = False,
	    connection_string=config.insights_connection_string)


	view_manager.register_exporter(exporter)

rng = [15,30,80]

def prompt():
	for i in rng:
	    mmap.measure_int_put(accuracy_measure, i)
	    mmap.record(tmap)
	    metrics = list(mmap.measure_to_view_map.get_metrics(datetime.utcnow()))
	    print(metrics[0].time_series[0].points[0])
	    time.sleep(5)

def main():
	x = 0

	while x < 5 :
		prompt()
		x+=1

if __name__ == "__main__":
    main()