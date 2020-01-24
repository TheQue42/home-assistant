#!/usr/bin/env python3

import json
import os, sys, re
import argparse

_scriptVersion=0.01


_FILE_DEV_REGISTRY="/var/lib/ha/.storage/core.device_registry"
_FILE_ENTITY_REGISTRY="/var/lib/ha/.storage/core.entity_registry"

def _createArgParser():
    cli = argparse.ArgumentParser(
            prog="PythonProg",
            description = "Default Description",
            epilog="This is a python script",
            )

    cli.add_argument('--version', "-V", action='version', version=F'%(prog)s {_scriptVersion}')
    #cli.add_argument('--out', "-o", nargs='?', default=sys.stdout)  #type=argparse.FileType('w')

    cli.add_argument('--nullcount', "-nc", default=3)
    cli.add_argument('--list-pattern', "-lp")  # List fields from registry files.
    cli.add_argument('--unify', "-U", help="match default unifi entries")  # List fields from registry files.

    fromWhere = cli.add_mutually_exclusive_group()
    fromWhere.add_argument('--device', "-d", action="store_true", default=False)
    fromWhere.add_argument('--stdin', "-i", action="store_true", default=False)
    fromWhere.add_argument('--file', "-f", dest="infile")
    fromWhere.add_argument('--entity', "-e", action="store_true", default=False) # This should be default...?

    howFilter = cli.add_mutually_exclusive_group()
    # USAGE: filter.py -p uuid:XX, plattform, dev (or -p X:uuid:".*aa"
    howFilter.add_argument('--pattern', "-p", nargs="*", metavar="key:filter")

    whatDoFilter = cli.add_mutually_exclusive_group()
    whatDoFilter.add_argument("--exclude", "-x", action="store_true", default=True)
    whatDoFilter.add_argument("--include", "-I", action="store_true", default=False)
    #whatDoFilter.add_argument('--list', "-l", help="list only", action="store_true")

    loggingDebug = cli.add_mutually_exclusive_group() # required=true if either cli-param is required
    loggingDebug.add_argument("--verbose", "-v", help="Increase verbosity", action='count')
    loggingDebug.add_argument("--quiet", "-q", help="Reduce verbosity", action='count')
    return cli



def printEntity(e, e_id, all_meta=False):
    for entity_key in e.keys():
        if re.match(r"unique_id|config_entry_id|device_id", entity_key) and not all_meta:
            continue
        print("[%s] Key: %s has value: [%s]" % (e_id, entity_key, e[entity_key]))
    print("")


def processEntities(args, jsonData):
    '''
    Process /var/lib/home-assistant/.storage/core.entity_registry
    '''
    fullCount = 0
    unifiCount = 0
    deleteCount = 0
    filteredData = dict()
    filteredData["data"] = dict()
    filteredData["data"]["entities"] = []
    deleteData = dict()
    deleteData["data"] = dict()
    deleteData["data"]["entities"] = []

    origCount = len(jsonData["data"]["entities"])

    if args.list_node :
        for entity in jsonData["data"]["entities"] :
            filterString1 = str(args.list_node) + "-"
            filterString2 = "node-" + str(args.list_node)
            if re.match(filterString1, entity["unique_id"]) or re.match(filterString2, entity["unique_id"]) :
                #printEntity(entity, fullCount, all_meta=True)
                print(json.dumps(entity, indent=1))
                print("")
                fullCount += 1

    if args.del_node :
        for entity in jsonData["data"]["entities"] :
            filterString1 = str(args.del_node) + "-"
            filterString2 = "node-" + str(args.del_node)
            if re.match(filterString1, entity["unique_id"]) or re.match(filterString2, entity["unique_id"]) :
                deleteData["data"]["entities"].append(entity)
                print(json.dumps(entity, indent=1))
                print("")
                deleteCount += 1
            else:
                filteredData["data"]["entities"].append(entity)
                fullCount +=1
        afterFile = open("/tmp/after.yaml", "w")
        delFile = open("/tmp/deleted.yaml", "w")
        print("-------------------")
        print("Filterd Count: {}, Deleted Count: {}, Original Count: {}".
                format(fullCount, deleteCount, origCount))
        json.dump(filteredData, afterFile, indent=2, sort_keys=True)
        afterFile.close()
        json.dump(deleteData, delFile, indent=2, sort_keys=True)
        delFile.close()

    if args.list_disabled : # Disabled_by is not empty 
        for entity in jsonData["data"]["entities"] :
            if entity["disabled_by"] :
                printEntity(entity, fullCount)
                print("")
                fullCount += 1
    
    if args.list_unifi != "dont" :
        for entity in jsonData["data"]["entities"] :
            if entity["platform"] == "unifi":
                # Should we only display the known2empty and is it one of those?
                if re.match(r"only", args.list_unifi) :
                    if re.match(r"device_tracker.unifi.*", entity["entity_id"]):
                        printEntity(entity, fullCount)
                        unifiCount += 1
                else :
                    printEntity(entity, fullCount)                                            
                fullCount += 1
        print("All Unifi Count: {}, Filtered Unifi Count: {}".format(fullCount, unifiCount))


    if args.strip_unifi != "dont" :
        '''
        here we've got entities[] with keys:
        - "config_entry_id": "7bfa7234010b419f956f6dbb9d72e966",
        - "device_id": "9f718999a08345db9123fd20c929344c",
        - "disabled_by": "user",
        - "entity_id": "sensor.fibaro_system_fgms001_zw5_motion_sensor_seismic_intensity",
        - "entity_id": "device_tracker.unifi_58_ef_39_a8_3a_9e_default",        
        - "name": "MS - Mancave - Seismic",
        - "platform": "zwave",
        - "unique_id": "3-72057594093257106"
        '''
        print("Will strip {} Unifi entries".format(args.strip_unifi))
        for entity in jsonData["data"]["entities"] :
            if entity["platform"] == "unifi" :
                # Should we only strip the empty, know-2-bad entries?
                if re.match(r"only", args.strip_unifi) and not re.match(r"device_tracker.unifi.*", entity["entity_id"]):
                    print("Adding: {} with name: {}".format(entity["entity_id"], entity["name"]))
                    filteredData["data"]["entities"].append(entity)
                    unifiCount += 1
            else:
                filteredData["data"]["entities"].append(entity)
            fullCount +=1
    
        print("Filtered list count: {}, Orig List Count: {}, Unifi Count: {}".
                format(len(filteredData["data"]["entities"]), origCount, unifiCount))
        newFile = open("/tmp/newfile.yaml", "w")
        print("-------------------")
        json.dump(filteredData, newFile, indent=2, sort_keys=True)
        newFile.close()
        print("-------------------")

def listFilterKeywords(which : str, jsonData : dict):
    searchList = []
    if "devices" in jsonData["data"]:
        searchList = jsonData["data"]["devices"]
    elif "entities" in jsonData["data"] :
        searchList = jsonData["data"]["entities"]
    else:
        print("Did not find either DEVICES or ENTITIES in", jsonData["data"].keys())

    keysFoundInList = [ key for key in searchList[0].keys()]
    #print("Keys", keysFoundInList)
    # This loop is probably unnecessary since all entries SHOULD have the SAME keys.
    foundAdditional = False
    for entry in searchList:
        for entryKey in entry.keys():
            if entryKey not in keysFoundInList:
                print("Adding new key", entry)
                foundAdditional = True
                keysFoundInList.append(entryKey)

    for k in keysFoundInList:
        print(f"Key: {k}")
    # TODO: Add printout of common values (use values["key"] = set())

def main(argv = None):
    _scriptName = sys.argv[0]
    cliArgs = _createArgParser()

    print(f"Arguments Will BE parsed by {sys.argv[0]}, and version:{_scriptVersion}")
    args = cliArgs.parse_args()
    print(args)

    input_source = ""
    jsonDataKey = ""
    if args.entity :
        input_source = _FILE_ENTITY_REGISTRY
    elif args.device:
        input_source = _FILE_DEV_REGISTRY

    elif args.stdin:
        input_source = sys.stdin
    elif args.infile is not None:
        input_source = args.infile

    print("Will read from:", input_source)

    jsonObj = {}
    if os.path.isfile(input_source) :
        try:
            yfile = open(input_source)
            jsonObj = json.load(yfile)
        except:
            print("Failed to open file")

    jsonDataKey = list(jsonObj["data"].keys())[0]
    count = len(jsonObj["data"][jsonDataKey])
    print(f"\nReading data for [{jsonDataKey}] Count: {count}\n")
    #sys.exit()
    if "entities" in jsonObj["data"].keys():
        listFilterKeywords("entities", jsonObj)
    elif "devices" in jsonObj["data"].keys():
        listFilterKeywords("devices", jsonObj )
    else :
        print("Unknown contents in file")

        
if __name__ == "__main__":
    sys.exit(main())




"""

Entity Registry Entry: /var/lib/ha/.storage/core.entity_registry     
    {
                "capabilities": null,
                "config_entry_id": "693fca7e7aa2446e9665416ff0f62de4",
                "device_class": null,
                "device_id": "1c52eda6d9654218bb48f9e5fcebb94f",
                "disabled_by": null,
                "entity_id": "device_tracker.unifi_cc_5e_03_4b_d3_09_default",
                "name": null,
                "platform": "unifi",
                "supported_features": 0,
                "unique_id": "cc:5e:03:4b:d3:09-default",
                "unit_of_measurement": null
    }
    Device registry entry: / var / lib / ha /.storage / core.device_registry
    {
        "area_id": null,
        "config_entries": [
            "693fca7e7aa2446e9665416ff0f62de4"
        ],
        "connections": [
            [
                "mac",
                "cc:5e:03:4b:d3:09"
            ]
        ],
        "id": "1c52eda6d9654218bb48f9e5fcebb94f",
        "identifiers": [],
        "manufacturer": null,
        "model": null,
        "name": null,
        "name_by_user": null,
        "sw_version": null,
        "via_device_id": null
    }
"""
