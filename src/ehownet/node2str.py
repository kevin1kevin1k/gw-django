# encoding: utf-8

def node2str(node_a,semantic_node_dict):
	if not semantic_node_dict:
		return node_a
	
	# ---------- define rule  ---------- 
	direct_cat=["content","target","possession","theme"]
	reverse_cat=["manner"]
	#reverse_particle_cat=["predication","qualification","taste","telic"]
	reverse_particle_cat=["taste","size","shape"]	
	reverse_use_cat=["instrument","means"]
	sname_reverse_particle_cat=["source"]
	location_cat=["location"]
	sname_location_cat=["domain"]

	sname_translate={"source":"來源","domain":"界"}

	semantic_list=semantic_node_dict.keys()

	#  ---------- start, intermediate, end  ---------- 
	#start
	start_candidate=["location","domain"]
	start=None
	start_node=None
	for cand in start_candidate:
		if cand in semantic_list:
			start=cand
			start_node=semantic_node_dict[cand]
			break

	#end
	end_candidate=["predication","telic","qualification"]
	end=None
	end_node=None
	for cand in end_candidate:
		if cand in semantic_list:
			end=cand
			end_node=semantic_node_dict[cand]		
			break

	# intermediate
	if start:
		semantic_node_dict.pop(start,None)
	if end:
		semantic_node_dict.pop(end,None)

	#  ---------- construct the string  ---------- 
	result=""

	if start in location_cat:
		result= "在" + start_node + "的"
	elif start in sname_location_cat:	
		result= "在" + start_node + sname_translate[start] + "的"
	
	###
	for i,semantic in enumerate(semantic_node_dict):
		node_b= semantic_node_dict[semantic]
		if semantic in direct_cat:
			result+= node_a + node_b
		elif semantic in reverse_cat:
			result+= node_b + node_a
		elif semantic in reverse_particle_cat:
			result+= node_b + "的" 
		elif semantic in reverse_use_cat:
			result+= "以" + node_b + node_a
		elif semantic in sname_reverse_particle_cat:
			result+= sname_translate[semantic] + "是" + node_b + "的" 
		elif semantic in location_cat:
			result+= "在" + node_b + "的" 
		elif semantic in sname_location_cat:
			result+= "在" + node_b + sname_translate[semantic] + "的" 
		else:
			result+= semantic_node_dict[semantic]
		#last element
		if i<len(semantic_node_dict)-1:
			conj = '或' if node_a == 'or' else '且'
			result+= conj

	if end:
		result+= end_node + "的" + node_a

	if result.endswith("的"):
		result+=node_a

	#domain location HumanPropensity
	return result

def main():
	print(node2str("醫治",{"target":"牙齒"}))
	print(node2str("管理",{"content":"機器"}))
	print(node2str("從事",{"manner":"賣力"}))
	print(node2str("食品",{"taste":"甜"}))
	print(node2str("專業人士",{"predication":"有法術"}))
	print(node2str("寫",{"instrument":"毛筆"}))
	print(node2str("食品",{"source":"花草"}))
	print(node2str("專業人士",{"domain":"音樂"}))
	print(node2str("專業人士", {"domain":"警","predication":"裁定"}))


	
if __name__ == '__main__':
		main()	