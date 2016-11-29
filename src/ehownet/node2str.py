def node2str(node_a,node_b,semantic):
	direct_cat=["content","target","possession","theme"]
	reverse_cat=["manner"]
	particle_cat=[]
	reverse_particle_cat=["predication","qualification","taste","telic"]
	reverse_use_cat=["instrument"]
	sname_reverse_particle_cat=["source"]

	sname_translate={"source":"來源"}

	result=""
	if semantic in direct_cat:
		result= node_a + node_b
	elif semantic in reverse_cat:
		result= node_b + node_a
	elif semantic in particle_cat:
		result= node_a + "的" + node_b
	elif semantic in reverse_particle_cat:
		result= node_b + "的" + node_a
	elif semantic in reverse_use_cat:
		result= "用" + node_b + node_a
	elif semantic in sname_reverse_particle_cat:
		result= sname_translate[semantic] + "是" + node_b + "的" + node_a

	#domain location HumanPropensity
	return result

def main():
	print(node2str("醫治","牙齒","target"))
	print(node2str("管理","機器","content"))
	print(node2str("從事","賣力","manner"))
	print(node2str("食品","甜","taste"))
	print(node2str("專業人士","有法術","predication"))
	print(node2str("寫","毛筆","instrument"))
	print(node2str("食品","花草","source"))
	
if __name__ == '__main__':
		main()	