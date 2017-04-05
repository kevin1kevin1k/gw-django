# encoding: utf-8
import re
import ancestors

def translate_eng_parentheses(s):
	eng_map = {'edge':'邊界', 'partOf':'一部份'}
	eng = s.split('(')[0]
	term = re.search(r'\((.*?)\)',s).group(1)
	if eng == 'and':
		#and({買},{賣})
		elements = term.split(',')
		result = ''.join(elements) 
	elif eng == 'or':
		#or({放置},{保存})
		elements = term.split(',')
		result = '或'.join(elements) 
	elif eng =='not':
		if '有' in term:
			result = '沒有'
		else:
			result = '無法' + term
	else:
		try:
			result = term + '的' + eng_map[eng]
		except Exception as e:
			result = term
	result = result.replace('{','').replace('}','')			
	return result

def node2str(node_a,semantic_node_dict):
	# print(node_a)
	# print(semantic_node_dict)
	if '(' in node_a and ')' in node_a:
		node_a = translate_eng_parentheses(node_a)
	for key,value in semantic_node_dict.items():
		if '(' in value and ')' in value:
			semantic_node_dict[key] = translate_eng_parentheses(value)

	if not semantic_node_dict: #沒有其他semantic的描述 直接回傳node_a (ex 螃蟹)
		return node_a
	
	# ---------- define rule  ---------- 
	direct_cat=["content","target","possession","theme",'patient','contrast','PatientProduct']
	reverse_cat=["manner"]
	#reverse_particle_cat=["predication","qualification","taste","telic"]
	reverse_particle_cat=["taste","size","length",'material','apposition']	
	reverse_use_cat=["instrument","means"]
	reverse_purpose_cat=["purpose"]
	sname_reverse_particle_cat=["source","shape",'ingredients']
	location_cat=["location",'position']
	sname_location_cat=["domain"]
	time_cat=["TimePoint"]
	quantity_cat =["quantity"]

	sname_translate={"source":"來源","domain":"界", "shape":"形狀", 'ingredients':'成份'}
	quantity_map={"1":"一", "2":"二","3":"三","4":"四","5":"五","6":"六","7":"七","8":"八","9":"九",}
	semantic_list=semantic_node_dict.keys()

	#  ---------- start, intermediate, end  ---------- 
	#start
	start_candidate= location_cat + sname_location_cat + time_cat
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
		elif semantic in reverse_purpose_cat:
			result+= "用來" + node_b
		elif semantic in sname_reverse_particle_cat:
			result+= sname_translate[semantic] + "是" + node_b + "的" 
		elif semantic in location_cat:
			result+= "在" + node_b + "的" 
		elif semantic in sname_location_cat:
			result+= "在" + node_b + sname_translate[semantic] + "的" 
		elif semantic in quantity_cat:
			result+= quantity_map[semantic_node_dict[semantic]] + "個" +node_a
		else:
			result+= semantic_node_dict[semantic]
		#last element
		if i<len(semantic_node_dict)-1:
			conj = '或' if node_a == 'or' else '且'
			result+= conj

	if end:
		if end == 'telic':
			result+= '用來' + end_node + "的" + node_a
		else:			
			result+= end_node + "的" + node_a
	if start:
		if start in location_cat:
			result= "在" + start_node  + result
		elif start in sname_location_cat:	
			result= "在" + start_node + sname_translate[start] + result
		elif start in time_cat:	
			result= "在" + start_node + node_a + result

	if result.endswith("的") :
		result+=node_a
	
	if node_a not in result and node_a not in ['and','or','not']:
		if ancestors.is_class(node_a):
			result= result + '的' + node_a
		else:
			result= result + node_a

	result = result.replace('在在','在')
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