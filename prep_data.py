import csv
import re
import sys
import json
from os import listdir
from os.path import isfile, join


class LocLoader:
    def __init__(self, file_name):
        self.file_name = file_name
        self.lat_index = 1 
        self.long_index = 2 
        self.name = 0 
        self.results = {}
        self.load()

    def load(self):
        csv_list = []
        with open(self.file_name, 'r') as f:
            for line in f:
                vals = line.split()
                geo = []
                geo.append(vals[self.lat_index].strip(", "))
                geo.append(vals[self.long_index].strip(", "))
                self.results[(vals[(self.name)]).strip(", ")] = geo 

class Data:
    def __init__(self, file_name, state_abbv, state_name, geo_vals):
        self.state_code = state_abbv
        self.state_name = state_name
        self.results_to_csv = []
        self.results_to_json = []
        self.geo_vals = geo_vals
        self.load(file_name)

    def load(self, file_name):
        csv_list = []
        with open(file_name, 'r') as f:
            reader = csv.reader(f)
            csv_list = list(reader)
            for line in csv_list:
                try:
                    float(line[0])
                    # s ample line
                    # 003,Baldwin County,357,4,2,0.6%,0,"74,285","4,986",15.0%
                    result = Result(line, self.geo_vals, self.state_code, self.state_name)
                    #self.results_to_csv.append(result.output_list) 
                    self.results_to_json.append(result.result_dict) 
                except:
                    continue

    def output_csv(self):
        with open(self.output_file, 'w') as f:
            header = "FIPS,County_Name,Num_Children_Tested,Percent_Children_Tested,Total_Confirmed_Cases,Percent_Children_Elevated_Blood,Total_Housing_Units,Pre1950_House,Pop_children_Under6,Percent_Under6_Poverty\n"
            f.write(header)
            for r in self.results_to_csv:
                f.write(str(r)+'\n') 


class Result:
    """
    This defines the data to be passed to ES
    Data schema is defined in 
    """
    def __init__(self, line, geo_vals, state_code, state_name):
        self.state_code = state_code
        self.state_name = state_name
        self.geo_vals = geo_vals
        self.result_dict = {} 
        self.fips = "None" 
        # set default variables , -1 means unreported
        # must differentiate between unreported and 0
        self.County_Name = "None"
        self.Num_Children_Tested = -1 
        self.Percent_Children_Tested = -1 
        self.Total_Confirmed_Cases = -1 
        self.Percent_Children_Elevated_Blood = -1
        self.Total_Housing_Units = -1
        self.Pre1950_House = -1
        self.Percent_Under6_Poverty = -1
        self.Pop_children_Under6 = -1
        self.Polygon = []
        self.parse_line(line) 

    def convert_percent(self, str_percent):
        str_percent = str_percent.strip('%')
        result_num = -1
        try:
            result_num = float(str_percent) / 100 
            result_num = format(result_num, '.2f')
        except:
            result_num = -1
        return result_num     

    def convert_num(self, str_number):
        str_number = str_number.replace(",", "")
        result_num = -1
        try:
            result_num = float(str_number)
        except:
            result_num = -1                        
        return result_num
 

    def parse_line(self, line):

        self.fips = line[0].strip("\"")
        self.County_name = line[1].replace("County", "").strip()
        self.Num_Children_Tested = self.convert_num(line[2]) 
        self.Percent_Children_Tested = self.convert_percent(line[3]).strip('\'') 
        self.Total_Confirmed_Cases = self.convert_num(line[4]) 
        self.Percent_Children_Elevated_Blood = self.convert_percent(line[5])
        self.Total_Housing_Units = self.convert_num(line[6])
        self.Pre1950_House = self.convert_num(line[7])
        self.Pop_children_Under6 = self.convert_num(line[8])
        self.Percent_Under6_Poverty  = self.convert_percent(line[9])

        flocation = {} 
        key = self.state_code + "_" + self.County_name
        if key in self.geo_vals:
            flocation['lat'] = float(self.geo_vals[key][0])
            flocation['lon'] = float(self.geo_vals[key][1])
        else:
            flocation['lat'] = -1 
            flocation['lon'] = -1
        
        self.result_dict['State'] = self.state_name 
        self.result_dict['COUNTY_NAME'] = self.County_name
        self.result_dict['FIPS'] = self.fips
        self.result_dict['NUM_CHILDREN_TESTED'] = self.Num_Children_Tested
        self.result_dict['PERCENT_CHILDREN_TESTED'] = self.Percent_Children_Tested
        self.result_dict['TOTAL_CONFIRMED_CASES'] = self.Total_Confirmed_Cases
        self.result_dict['PERCENT_CHILDREN_ELEVATED_BLOOD'] = float(self.Percent_Children_Elevated_Blood)
        self.result_dict['location'] = flocation 
        self.result_dict['TOTAL_HOUSING_UNITS'] = self.Total_Housing_Units
        self.result_dict['Pre1950_House'] = self.Pre1950_House
        self.result_dict['Pop_children_Under6'] = self.Pop_children_Under6
        self.result_dict['Percent_Under6_Poverty'] = float(self.Percent_Under6_Poverty) 




if __name__ == "__main__":
    args = sys.argv
    loader = LocLoader(args[1])
    dir_path = args[2]
    onlyfiles = [f for f in listdir(dir_path) if isfile(join(dir_path, f))]    
    full_results = []
    for f in onlyfiles:
        name_vals = f.split("_")
        state_abbv = name_vals[0]
        state_name = name_vals[1]
        file_name = dir_path + "/" + f
        data = Data(file_name, state_abbv, state_name, loader.results)
        full_results = full_results + data.results_to_json

    count = 0
    with open(args[3], 'w') as f:
        for i, r in enumerate(full_results):
            count = i+1
            str1 = "{ \"index\" : { \"_index\" : \"all_county_data\", \"_type\" : \"allcountydata\", \"_id\" : \"" + str(count) + "\" } }"
            f.write(str1+'\n')
            f.write(json.dumps(r)+'\n')

