import logging
import config
import time
import random
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


stats = stats_module.stats
view_manager = stats.view_manager
stats_recorder = stats.stats_recorder

errors_measure = measure_module.MeasureInt("number_errors",
                                           "Number of wrongly detected information",
                                           "requests")
success_measure = measure_module.MeasureInt("number_success",
                                           "Number of successfull language queries",
                                           "requests")

score_measure = measure_module.MeasureInt("user_score",
									   "Score provided by the user at the end of each discussion",
									   "score")

accuracy_measure = measure_module.MeasureInt("total_accuracy",
                                           "Overall Bot Accuracy",
                                           "%")
errors_view = view_module.View("number_errors",
                               "Count of the number of wrongly detected information",
                               [],
                               errors_measure,
                               aggregation_module.CountAggregation())

success_view = view_module.View("number_success",
                               "Count of the number of user confirmation prompts answered positively",
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

#mmap = stats_recorder.new_measurement_map()

#tmap = tag_map_module.TagMap()

exporter = metrics_exporter.new_metrics_exporter(
	enable_standard_metrics = False,
    connection_string=config.insights_connection_string)


view_manager.register_exporter(exporter)


def save_success_or_failure(success=True):

	mmap = stats_recorder.new_measurement_map()
	tmap = tag_map_module.TagMap()

	if not success:

		mmap.measure_int_put(errors_measure, 1)
		mmap.record(tmap)

	else:
		mmap.measure_int_put(success_measure, 1)
		mmap.record(tmap)

	metrics = list(mmap.measure_to_view_map.get_metrics(datetime.utcnow()))
	if len(metrics) > 1:
		errors = metrics[0].time_series[0].points[0].value.value
		successes = metrics[1].time_series[0].points[0].value.value
		return errors, successes
	else:
		#Not enough information, return 1/1 for baseline 50% accuracy
		return 1,1



def save_accuracy(err, succ):

	mmap_acc = stats_recorder.new_measurement_map()
	tmap_acc = tag_map_module.TagMap()

	accuracy = int(100*succ / (err+succ))

	mmap_acc.measure_int_put(accuracy_measure, accuracy)
	mmap_acc.record(tmap_acc)


def save_request_data(success=True):
	err, succ = save_success_or_failure(success)
	save_accuracy(err,succ)

def save_user_score(score):
	mmap_score = stats_recorder.new_measurement_map()
	tmap_score = tag_map_module.TagMap()

	mmap_score.measure_int_put(score_measure, score)
	mmap_score.record(tmap_score)

# def prompt():

# 	mmap = stats_recorder.new_measurement_map()

	

# 	# random_user_score = random.randint(1,5)
# 	# mmap.measure_int_put(user_score, random_user_score)


# 	if random.randint(0,1) == 0:
# 		print("Error")
# 		mmap.measure_int_put(errors_measure, 1)
# 		tmap = tag_map_module.TagMap()
# 		mmap.record(tmap)
# 	#Calculating accuracy

# 	else:
# 		print("Success")
# 		mmap.measure_int_put(success_measure, 1)
# 		tmap = tag_map_module.TagMap()
# 		mmap.record(tmap)

# 	metrics = list(mmap.measure_to_view_map.get_metrics(datetime.utcnow()))
# 	if len(metrics) > 1:
# 		errors = metrics[0].time_series[0].points[0].value.value
# 		successes = metrics[1].time_series[0].points[0].value.value
# 		print(errors, "    /   ", successes)
# 		time.sleep(15)
# 		return errors, successes
# 	# #Only triggered if both successes and errors are defined
# 	# if (len(error_metrics)!= 0) & (len(success_metrics)!=0) :

# 	# 	errors = error_metrics[0].time_series[0].points[0].value.value
# 	# 	successes = success_metrics[0].time_series[0].points[0].value.value
# 	# 	accuracy = int(100*successes / (errors + successes))

# 	# 	mmap_acc.measure_int_put(accuracy_measure, accuracy)
# 	# 	mmap_acc.record(tmap)

# 	# 	print("Successes : {}, Errors : {},  Accuracy : {}, User Score: {}".format(successes,
# 	# 	 errors, accuracy, random_user_score))
# 	# #print(metrics[0].time_series[0].points[0].value.value)
# 	# #print(metrics[0].time_series[0].points[0].value)
# 	time.sleep(15)
# 	return 1, 1

# def main():
# 	x = 0
# 	while x < 10 :
# 		print("X = ", x)
# 		err, succ = prompt()
# 		save_accuracy(err, succ)
# 		save_user_score()
# 		x+=1



def main():
	logger = configure_logger()
	properties = {'custom_dimensions': {'key_1': 'value_1', 'key_2': 'value_2'}}

	x = 0

	while x < 1:
		x+=1
		# Use properties in exception logs
		try:
		    result = 1 / 0  # generate a ZeroDivisionError
		except Exception:
		    logger.exception('Captured an exception.', extra=properties)

if __name__ == "__main__":
    main()