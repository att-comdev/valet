_REGION_CHARS = 3   # set in the config
_RACK_RECOG_CHARS = ['r']   # set in the config
_NODE_RECOG_CHARS = ['a', 'c', 'u', 'f', 'o', 'p', 's']   # set in the config

#host_name = "ksc15r005c009"
#host_name = "pdk20r05o112"

#host_name = "pd2r1a1"
#host_name = "pdkw2r1a1"

#host_name = "pdk2ra"
#host_name = "pdk2rza"
#host_name = "pdk2z1a2"

#host_name = "pdk2r1o"
#host_name = "pdk2r1oc"
#host_name = "pdk2r1oz"
#host_name = "pdk2r1o112c2"
#host_name = "pdk2r1o112z"

#host_name = "qos101"
host_name = "simu0r0c2"

print "input name=",host_name

region_clli = host_name[:_REGION_CHARS]
print "region_clli=",region_clli

region_name = None
rack_name = None
node_type = None

validated_name = True
num_of_fields = 0

index = 0
end_of_region_index = 0
end_of_rack_index = 0
index_of_node_type = 0

for c in host_name:
    if index >= _REGION_CHARS:
        print "index = {}, char = {}".format(index, c)

        if c == '0' or \
           c == '1' or \
           c == '2' or \
           c == '3' or \
           c == '4' or \
           c == '5' or \
           c == '6' or \
           c == '7' or \
           c == '8' or \
           c == '9':
            pass
        else:
            if index == _REGION_CHARS:
                print "invalid region name = ", (host_name[:index] + c)
                validated_name = False
                break

            if end_of_region_index == 0:
                if c not in _RACK_RECOG_CHARS:
                    print "invalid rack_char = ", c
                    validated_name = False
                    break 

                end_of_region_index = index
                num_of_fields += 1

            if index == (end_of_region_index + 1):
                print "invalid rack name = ", (host_name[:index] + c)
                validated_name = False
                break

            #if end_of_rack_index == 0 or end_of_rack_index == end_of_region_index:
            if end_of_rack_index == 0 and index > (end_of_region_index + 1):
                end_of_rack_index = index
                num_of_fields += 1

            #if end_of_rack_index > end_of_region_index:
            if node_type == None and end_of_rack_index > 0:
                node_type = c
                if node_type not in _NODE_RECOG_CHARS:
                    print "invalid node_char = ", c
                    validated_name = False
                    break
                index_of_node_type = index
                num_of_fields += 1

            if index_of_node_type > 0 and index > index_of_node_type:
                num_of_fields += 1
                print "too many fields = ", num_of_fields
                break 

    index += 1

if not index > (index_of_node_type + 1):
    print "invalid node name = ", host_name[:index]
    exit(2)

if num_of_fields != 3:
    print "invalid number of identification fields = ",num_of_fields
    validated_name = False
    exit(2)

if validated_name == False:
    print "invalid naming convention"
    # create mockup rack & region
    exit(2)

region_name = host_name[:end_of_region_index]
print "region=",region_name
rack_name = host_name[:end_of_rack_index]
print "rack=",rack_name
print "node_type=",node_type

     

    

