import sys, ast, imp

def parseDataFeed_requirements(tile_data):
	requirements = tile_data["requirements"].split('<req_split>')
	
	formattedRequirementResources = {}

	for req in requirements:
		req = req.split('=')
		
		req_type = req[0]
		req_uri = req[1]

		if req_type == "template_file":
			formattedRequirementResources["template_file"] = req_uri
		elif req_type == "query_file":
			formattedRequirementResources["query_file"] = req_uri
		elif req_type == "helper_script":
			formattedRequirementResources["helper_script"] = req_uri
		elif req_type == "data_sources":
			formattedRequirementResources["data_sources"] = req_uri

	return formattedRequirementResources


	



def loadHelperScript(file_uri):
	data_feed_tile = imp.load_source('data_feed_tile', 'modules/database/helper_scripts/data_feed_tile.py')


	class_name = file_uri.split('.')[0]

	helper_script = imp.load_source(class_name, 'modules/database/helper_scripts/' + file_uri)
	
	#load the actual class object
	if hasattr(helper_script, class_name):
		helper_script_class = getattr(helper_script, class_name)
		helper_script = helper_script_class  #handle to class, not an instance

	return helper_script