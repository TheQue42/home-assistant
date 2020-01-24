#!/usr/bin/env python3

import json
import os, sys, re
import argparse
from time import sleep

from samba.dcerpc.smb_acl import entry

_scriptVersion=0.1


_FILE_DEV_REGISTRY="/var/lib/ha/.storage/core.device_registry"
_FILE_ENTITY_REGISTRY="/var/lib/ha/.storage/core.entity_registry"
_FILE_OUT_STRIPPED="./stripped.json"
_FILE_OUT_CLEANED="./cleaned.json"
LogLevel = 0


def printEntity(e, e_id, all_meta=False):
    for entity_key in e.keys():
        if re.match(r"unique_id|config_entry_id|device_id", entity_key) and not all_meta:
            continue
        print("[%s] Key: %s has value: [%s]" % (e_id, entity_key, e[entity_key]))
    print("")


def matchEntry(entry, entry_filters : dict) -> bool:
    """ TODO """
    #print("CCC", entry["connections"], type(entry["connections"]))
    assert isinstance(entry_filters, dict) and len(entry_filters) > 0
    # TODO: Print warning if a filterKey matches multiple entryKeys? ==> WILL OFTEN AUTOFAIL!
    for filterKey in entry_filters.keys():
        filterKeyFound = False
        for entryKey in entry.keys():
            if re.search(filterKey, entryKey, re.IGNORECASE):
                if LogLevel > 3:
                    print(f"KeyCheck [{entryKey}] against [{filterKey}] - MATCH")
                filterKeyFound = True
                # Here, we've found user-filter-key that matches a key for a specific entry.
                # If the values for those keys dont match, this entry will never match.
                # (But the entry may be empty)
                if isinstance(entry[entryKey], dict):
                    # Recursively search datastructure. TODO:
                    pass
                elif isinstance(entry[entryKey], list) or isinstance(entry[entryKey], tuple) :
                    # Recursively search datastructure. TODO:
                    pass
                elif isinstance(entry[entryKey], int):
                    if entry[entryKey] != int(entry_filters[filterKey]):
                        print("ValueFail:", entry[entryKey], entry_filters[filterKey])
                    pass
                else: # String Datatype (TODO:Float...)
                    if re.search("null", entry_filters[filterKey], re.IGNORECASE):
                        if entry[entryKey] is None or len(entry[entryKey]) == 0:
                            continue
                        else:
                            return False
                    else:
                        entryValue = entry[entryKey] if entry[entryKey] is not None else ""
                        if not re.search(entry_filters[filterKey], entryValue):
                            if LogLevel > 3:
                                print(f"ValueCheck [{entryValue}] against [{entry_filters[filterKey]}] - MIS-matches", )
                            return False
                        else:
                            if LogLevel > 2: print(f"ValueCheck [{entryValue}] against [{entry_filters[filterKey]}] - MATCHES", )
            else:
                if LogLevel > 2: print(f"KeyCheck [{entryKey}] against [{filterKey}] == MISmatch")

        if not filterKeyFound:
            if LogLevel > 0: print(f"Filterkey Did NOT match any entry-key: [{filterKey}]")
            # The user specified at least one key:value, but it wasn't found, so the entry cant match!
            return False
        else:
            # So filter key WAS found, but there are more filterKeys
            pass

    # If no filters for stripping matches...
    return True


def copyAllButEntries(orgDict: dict(), entry_key: str) -> dict:
    '''
    Dict structure is:
    '''
    copyOfDict = dict()
    # Normally "key", "data", "version"
    for key in orgDict.keys():
        assert isinstance(key, str)
        if key == "data" :
            copyOfDict[key] = {}
            assert isinstance(orgDict[key], dict)
            dataKeys = list(orgDict[key].keys())
            assert len(dataKeys) == 1, "There should only be a single key here"
            assert dataKeys[0] == entry_key
            assert isinstance(orgDict[key][entry_key], list)
            copyOfDict[key][entry_key] = []
        else:
            copyOfDict[key] = orgDict[key]
    return copyOfDict


def processEntities(jsonData: dict(), entry_key: str, entryFilters: dict, **kwargs):
    '''
    Process /var/lib/home-assistant/.storage/core.{jsonKey}_registry
    '''

    fullCount = 0
    stripCount = 0
    whatsLeft = copyAllButEntries(jsonData, entry_key)
    filteredData = copyAllButEntries(jsonData, entry_key)
    entriesToKeep = []
    entiresToStrip= []
    origCount = len(jsonData["data"][entry_key])
    print("Will filter with filters", entryFilters)
    #sleep(2)
    for entry in jsonData["data"][entry_key] :
        if matchEntry(entry, entryFilters):
            if LogLevel > 1: printEntity(entry, "Stripping\n", json.dumps(entry, indent=2, sort_keys=True))
            entiresToStrip.append(entry)
        else:
            #out = json.dumps(entry, indent=2, sort_keys=True)
            if LogLevel > 1: printEntity(entry, "Appending\n", json.dumps(entry, indent=2, sort_keys=True))
            entriesToKeep.append(entry)
        fullCount +=1
    whatsLeft["data"][entry_key] = entriesToKeep
    filteredData["data"][entry_key] = entiresToStrip
    print(f"\nOrig entry Count: {origCount}, Current (filtered) count: {len(entriesToKeep)}, StripCount: {len(entiresToStrip)}\n")

    cleanedFile = open(_FILE_OUT_CLEANED, "w")
    strippedFile = open(_FILE_OUT_STRIPPED, "w")
    #print("-------------------")
    json.dump(whatsLeft, cleanedFile, indent=2, sort_keys=True)
    json.dump(filteredData, strippedFile, indent=2, sort_keys=True)
    cleanedFile.close()
    strippedFile.close()
    os.system("ls -lF *.json")
    #print("-------------------")


def listFilterKeywords(dataKey: str, jsonData : dict):
    """
    This function will parse the Json-File and print out the keys for each entitity[dict], so make it easier
    to create match-patterns with --pattern <key:value>

    :param dataKey:
    :param jsonData:
    :return:
    """

    assert isinstance(jsonData["data"], dict) and dataKey in jsonData["data"].keys(), "Invalid DICT for parsing"
    searchList = jsonData["data"][dataKey]

    keysFoundInList = [key for key in searchList[0].keys()]
    #print("Keys", keysFoundInList)

    # This loop is probably unnecessary since all entries SHOULD have the SAME keys, but, better safe than sorry.
    foundAdditional = False
    for entry in searchList:
        for entryKey in entry.keys():
            if entryKey not in keysFoundInList:
                print("SOME ENTRIES HAVE DIFFERENT AMOUNT OF KEYS", entry)
                sleep(2.0)
                foundAdditional = True
                keysFoundInList.append(entryKey)

    for k in keysFoundInList:
        print(f"Key: {k}")
    # TODO: Add printout of common values (use values["key"] = set())

def _createArgParser():
    cli = argparse.ArgumentParser(
            #prog="Ha-Storage-Filter",
            description = "This program will filter Home-assistants .storage/-files",
            epilog="""
            Use this program at your OWN RISK. For safety sake, it will never overwrite the original files.\
            
            Additionally, it is currently only capable of filtering string-data in the json files\
            """)

    cli.add_argument('--version', "-V", action='version', version=F'%(prog)s {_scriptVersion}')
    #cli.add_argument('--out', "-o", nargs='?', default=sys.stdout)  #type=argparse.FileType('w')

    cli.add_argument('--nullcount', "-nc", default=3)
    cli.add_argument('--list-pattern', "-l", "-lp", nargs="?", default=None, const=".*")
    cli.add_argument('--unify', "-U", help="match default unifi entries")  # List fields from registry files.

    fromWhere = cli.add_mutually_exclusive_group(required=True)
    fromWhere.add_argument('--device', "-d", action="store_true", default=False)
    fromWhere.add_argument('--stdin', "-i", action="store_true", default=False)
    fromWhere.add_argument('--file', "-f", dest="infile")
    fromWhere.add_argument('--entity', "-e", action="store_true", default=False) # This should be default...?

    #howFilter = cli.add_mutually_exclusive_group()
    # USAGE: filter.py -p uuid:XX, plattform, dev (or -p X:uuid:".*aa"
    cli.add_argument('--pattern', "-p", nargs="*", metavar="key:filter", required=True)

    whatDoFilter = cli.add_mutually_exclusive_group()
    whatDoFilter.add_argument("--exclude", "-x", action="store_true", default=True)
    whatDoFilter.add_argument("--include", "-I", action="store_true", default=False)
    #whatDoFilter.add_argument('--list', "-l", help="list only", action="store_true")

    loggingDebug = cli.add_mutually_exclusive_group() # required=true if either cli-param is required
    loggingDebug.add_argument("--verbose", "-v", help="Increase verbosity", action='count', default=0)
    loggingDebug.add_argument("--quiet", "-q", help="Reduce verbosity", action='count', default=0)
    return cli


def main(argv = None):
    _scriptName = sys.argv[0]
    cliArgs = _createArgParser()
    args = cliArgs.parse_args()
    #print(args)

    global LogLevel
    LogLevel += int(args.verbose) - args.quiet
    #print(f"Arguments Will BE parsed by {sys.argv[0]}, and version:{_scriptVersion}, LogLevel {LogLevel}")
    input_source = ""
    dataKey = ""
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

    topKeys = list(jsonObj.keys())
    dataKeys = list(jsonObj["data"].keys())
    dataKey = dataKeys[0]
    count = len(jsonObj["data"][dataKey])

    #print(f"\nReading data for [{dataKey}] Count: {count} With Data Keys: {dataKeys}, and TopKeys {topKeys}")
    # for w in topKeys:
    #     if isinstance(jsonObj[w], dict):
    #         print(f"Key [{w}]: Type [{type(jsonObj[w])}] Id: {jsonObj[w].keys()}\n")
    #     else:
    #         print(f"Key [{w}], Id: {jsonObj[w]}\n")
    if args.list_pattern :
        listFilterKeywords(dataKey, jsonObj)
    else:
        patternHash = dict()
        for p in args.pattern:
            key, value = p.split(":")
            patternHash[key] = value
        processEntities(jsonObj, dataKey, patternHash ) # {"plat" : "zwave", "_id": "default"}
    print(f"\nCompleted processing. You should now REALLY compare the files with the original. Like: \n"
          f"kdiff3 {input_source} {_FILE_OUT_CLEANED}")

if __name__ == "__main__":
    sys.exit(main())

