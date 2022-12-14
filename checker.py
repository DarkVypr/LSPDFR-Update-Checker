import os
import re
from pprint import pprint
from packaging import version
import requests
import json

with open("./config.json") as config:
    config = json.load(config)

with open("./ids.json") as ids:
    ids = json.load(ids)

# Clear The Terminal After Every Run
os.system("cls")
print()


def compareVersions(inst, ltst):
    try:
        inst = version.parse(inst)
        ltst = version.parse(ltst)
        if ltst > inst:
            return False
        return True
    except:
        print()
        print(
            f"\033[91mISSUE PARSING VERSION NUMBER \033[1minst: {inst} ltst: {ltst}\033[0m")
        print()
        return False


def searchFiles(files):
    r = re.compile("^(.*)RagePluginHook(.*)?.log$", re.I)
    searchedFiles = list(filter(r.match, files))
    return searchedFiles


def findStart(log):
    findStart = re.compile("(.*)(Folder)\s(is)\s((.*)plugins\\\lspdfr)")
    startLine = list(filter(findStart.match, log))
    if not startLine:
        raise Exception(
            '\033[93mPlayer never went on duty or loaded any plugins. Manual review sugested.\033[0m')
        exit(0)
    return startLine[0]


def findEnd(log):
    findEnd = re.compile("(.*)\sLSPD First Response\:\sCreating plugin(.*)")
    endLine = list(filter(findEnd.match, log))
    if not endLine:
        raise Exception(
            '\033[91mLSPDFR never created any plugins, it just found them. Manual review sugested.\033[0m')
        exit(1)
    return endLine[0]


def getNameVersion(plugins):
    trashRegexPlugName = re.compile("(.*)\sLSPD First Response\:\s")
    trashRegexVersion = re.compile("Version\=")
    cleanedList = []
    for i in plugins:
        cleanedList.append(i.split(', ')[0:2])
    for i in cleanedList:
        i[0] = re.sub(trashRegexPlugName, '', i[0])
        versionNumber = re.sub(trashRegexVersion, '', i[1])
        i[1] = versionNumber
    return cleanedList

# Base game version checkers


def checkRAGEVersion(log):
    rageVersionR = re.compile(
        "(.*)RAGE\sPlugin\sHook(.*)for(.*)", re.IGNORECASE)
    rageVersion = list(filter(rageVersionR.match, log))
    if not rageVersion:
        raise Exception(
            "\033[91mRAGEPluginHook version was never in log. Manual review required. :(\033[0m")
        exit(1)
    rageVersionRClean = re.compile(
        "((.*)Version\:\sRAGE\sPlugin\sHook\sv)|(\sfor\s(.*))", re.IGNORECASE)
    rageVersion = re.sub(rageVersionRClean, '', rageVersion[0])
    check = compareVersions(rageVersion, config["main"]["rage"])
    if check:
        return f"\033[92mRAGEPluginHook version is: \033[1m{rageVersion} (Latest)\033[0m"
    return "\033[91mRAGEPluginHook version is: \033[1m{}, Current: \033[1m{}. (<!> OUTDATED <!>).\033[0m".format(rageVersion, config["main"]["rage"])


def checkGTAVersion(log):
    gtaVersionR = re.compile("(.*)Product\sversion\:(.*)", re.IGNORECASE)
    gtaVersion = list(filter(gtaVersionR.match, log))
    if not gtaVersion:
        raise Exception(
            "\033[91mGTA 5 version was never in log. Manual review required (Probably a code error). :(\033[0m")
        exit(1)
    gtaVersionRClean = re.compile("(.*)Product\sversion\:\s", re.IGNORECASE)
    gtaVersion = re.sub(gtaVersionRClean, '', gtaVersion[0])
    check = compareVersions(gtaVersion, config["main"]["gta"])
    if check:
        return f"\033[92mGTA 5 version is: \033[1m{gtaVersion} (Latest)\033[0m"
    return "\033[91mGTA 5 version is: \033[1m{}, Current: \033[1m{}. (<!> OUTDATED <!>).\033[0m".format(gtaVersion, config["main"]["gta"])


def checkLSPDFRVersion(log):
    lspdfrVersionR = re.compile(
        "(.*)LSPD\sFirst\sResponse\:\s\[INFO\]\sRunning\sLSPD\sFirst\sResponse\s(.*)", re.IGNORECASE)
    lspdfrVersion = list(filter(lspdfrVersionR.match, log))
    if not lspdfrVersion:
        raise Exception(
            "\033[91mLSPDFR version was never in log. Manual review required (Never Loaded the Plugin). :(\033[0m")
        exit(1)
    lspdfrVersionRClean = re.compile("((.*)\()|\)", re.IGNORECASE)
    lspdfrVersion = re.sub(lspdfrVersionRClean, '', lspdfrVersion[0])
    check = compareVersions(lspdfrVersion, config["main"]["lspdfr"])
    if check:
        return f"\033[92mLSPDFR version is: \033[1m{lspdfrVersion} (Latest)\033[0m"
    return "\033[91mLSPDFR version is: \033[1m{}, Current: \033[1m{}. (<!> OUTDATED <!>).\033[0m".format(lspdfrVersion, config["main"]["lspdfr"])


def checkNATIVEUIVersion(log):
    nativeVersionR = re.compile(
        "((.*)RageNativeUI\sinstalled\sversion\:(.*))|((.*)RAGENativeUI\sVersion\:(.*))", re.IGNORECASE)
    nativeVersion = list(filter(nativeVersionR.match, log))
    if not nativeVersion:
        return "\033[93mRAGENativeUI.dll version is not included in log. Verify version with user.\033[0m"
    nativeVersionRClean = re.compile(
        "((.*)RageNativeUI\sinstalled\sversion\:\s)|((.*)RAGENativeUI\sVersion\:\s)", re.IGNORECASE)
    nativeVersion = re.sub(nativeVersionRClean, '', nativeVersion[0])
    check = compareVersions(nativeVersion, config["main"]["nativeui"])
    if check:
        return f"\033[92mRAGENativeUI.dll version is: \033[1m{nativeVersion} (Latest)\033[0m"
    return "\033[91mRAGENativeUI.dll version is: \033[1m{}, Current: \033[1m{}. (<!> OUTDATED <!>).\033[0m".format(nativeVersion, config["main"]["nativeui"])


def checkForKnownIssues(fulllog):
    issues = []
    for i in config["flags"]:
        r = re.compile(i["r"], flags=re.S | re.M | re.I)
        search = re.findall(r, fulllog)
        if len(search) < 1:
            continue
        search = list(dict.fromkeys(search))
        if i["smart"]:
            rSmart = re.compile(i["smart"])
            for j in search:
                smartSearch = re.findall(rSmart, j)
                if not smartSearch:
                    continue
                issues.append(f'{i["desc"]} {smartSearch[0]}')
            continue
        issues.append(i["desc"])
    issues = list(dict.fromkeys(issues))
    return issues


def removePluginErrors(plugins):
    goodPlugins = []
    r = re.compile(
        "^(.*)(LSPD First Response: )(.*?, )(Version=\d+\.\d+\.\d+\.\d+, )(Culture=.*?, )(PublicKeyToken=)(\w|\d)*$", re.I)
    for i in plugins:
        if re.match(r, i):
            goodPlugins.append(i)
        continue
    return goodPlugins


def getCommandLine(log):
    r = re.compile(
        "(?:.*Command line option\s)(?:\"|'|-)(.*?)(?:'|\")?(?:\s.*)")
    options = re.findall(r, log)
    return options


def timeoutThresh(log):
    timeout = re.findall("(?:.*?Read value:\s)(\d{5})", log)
    if not timeout:
        return '(None)'
    return timeout[0]

# Clean separator.
separator = "\n\n----------\n\n"

files = os.listdir('./')
logExists = searchFiles(files)

if not logExists:
    raise Exception(
        '\033[91mThere is no log file in this folder; Drop one in. :P\033[0m')

with open('./' + logExists[0], 'r', encoding="utf8") as log:
    fulllog = log.read()
    log = fulllog.split('\n')

# Check Log for small details that might be useful.
commandLine = getCommandLine(fulllog)
if len(commandLine) > 0:
    commandLine = ', '.join(list(dict.fromkeys(commandLine)))
else:
    commandLine = '(None)'

thresh = timeoutThresh(fulllog)

print('\033[4m\033[1mLOG DETAILS:\033[0m')
print()
print('\033[1m\033[92mCommand Line Options:\033[0m', f"\033[1m{commandLine}\033[0m")
print()
print('\033[1m\033[92mPlugin Timeout Threshold:\033[0m', f"\033[1m{thresh}\033[0m")
print(separator)

# Check Log for Common Shit & Flag It If Found.
print('\033[4m\033[1mCHECKING FOR KNOWN LOG ISSUES:\033[0m')
issues = checkForKnownIssues(fulllog)
if len(issues) < 1:
    print("\n\033[92m\033[1mNo Issues Detected\033[0m")
else:
    for i in issues:
        print("\n" + f"\033[91m\033[1m{i}\033[0m")
print(separator)

# Start Update Checking
print('\033[4m\033[1mCHECKING BASE GAME VERSIONS:\033[0m')
print()
print(checkGTAVersion(log))
print(checkRAGEVersion(log))
print(checkLSPDFRVersion(log))
print()
print(checkNATIVEUIVersion(log))

startLine = findStart(log)
endLine = findEnd(log)

startIndex = log.index(startLine)+1
endIndex = log.index(endLine)

section = log[startIndex:endIndex]

section = removePluginErrors(section)

pluginVersions = getNameVersion(section)

print(separator)
print('\033[4m\033[1mCHECKING PLUGIN VERSIONS:\033[0m')
print()
print("Detected", len(pluginVersions), "plugins..")
print(separator)

lspdfrRegex = re.compile(
    "https:\/\/www.lcpdfr.com\/downloads\/gta5mods\/(.*)\/(\d+)-(.*)")

removal = []
# Plugins that aren't blacklisted or hardcoded, and don't have an ID. They will error out if checked, never use them.
badPlugins = []
ignored = []
incorrect = []

# Searches for the plugin to get the ID from JSON file, then appends it to the list as the 2nd index.
for i in pluginVersions:
    if i[0] in config["deprecated"]:
        if config["deprecated"][i[0]]:
            badPlugins.append(i[0])
            removal.append(i[0] + ", " + config["deprecated"][i[0]])
        else:
            badPlugins.append(i[0])
            removal.append(i[0])
        continue
    for j in config["incorrect"]:  # Checks if the plugin is installed wrong.
        if i[0] == j["name"]:
            info = f"{i[0]}, Current Folder: GTAV/plugins/LSPDFR - Correct Folder: {j['path']}" if j[
                'path'] else f"{i[0]}, Current Folder: GTAV/plugins/LSPDFR - Correct Folder: [Unknown]"
            incorrect.append(info)
            badPlugins.append(i[0])
        continue
    if i[0] in config["blacklist"] or config["hardcoded"].get(i[0]) or i[0] in badPlugins:
        continue
    if not ids.get(i[0]):
        badPlugins.append(i[0])
        ignored.append(i[0] + ", (Ignore because: No ID available)")
        continue
    i.append(ids[i[0]])

update = []
ok = []

# Searches for versions according to the LCPDFR.com API, and compares them against the installed version. Also manages bad plugins and incorrectly installed plugins.
for i in pluginVersions:
    print(i)
    if i[0] in badPlugins:
        continue
    if i[0] in config["hardcoded"] or i[0] in config["blacklist"]:
        if i[0] in config["hardcoded"]:
            latestVersion = config["hardcoded"][i[0]]
            check = compareVersions(i[1], latestVersion)
            if check:
                ok.append(
                    i[0] + f", Installed: {i[1]} - Latest: {latestVersion} \033[93m[HARDCODED VERSION #]\033[0m")
                continue
            update.append(
                i[0] + f", Installed: {i[1]} - Latest: {latestVersion} \033[93m[HARDCODED VERSION #]\033[0m")
            continue
        else:
            ignored.append(i[0] + ", (Ignore because: Blacklisted)")
            continue
    pluginInfo = requests.get(
        f'https://www.lcpdfr.com/applications/downloadsng/interface/api.php?fileId={i[2]}&textOnly=true&do=checkForUpdates',
    )
    if pluginInfo.status_code >= 500:
        ignored.append(
            i[0] + ", (Ignore because: Error getting version from API. >=500 error.)")
        continue
    latestVersion = pluginInfo.text
    check = compareVersions(i[1], latestVersion)
    if check:
        ok.append(
            i[0] + f", Installed: {i[1]} - Latest: {latestVersion}")
        # time.sleep(1)
        continue
    update.append(
        i[0] + f", Installed: {i[1]} - Latest: {latestVersion}")
    # time.sleep(1)

# Make it all pretty
print(separator)
if len(ok) > 0:
    print("\033[1m\033[4mThe following plugins \033[92mare up-to-date:\033[0m")
    print()
    print('\n'.join(ok))
    print(separator)
if len(update) > 0:
    print("\033[1m\033[4mThe following plugins \033[93mneed to be updated:\033[0m")
    print()
    print('\n'.join(update))
    print(separator)
if len(removal) > 0:
    print("\033[1m\033[4mThe following plugins \033[91mneed to be removed as they are deprecated, issue-ridden, or redundant:\033[0m")
    print()
    print('\n'.join(removal))
    print(separator)
if len(incorrect) > 0:
    print(
        "\033[1m\033[4mThe following plugins \033[96mare installed incorrectly:\033[0m")
    print()
    print('\n'.join(incorrect))
    print(separator)
if len(ignored) > 0:
    print("\033[1m\033[4mThe following plugins \033[94mwere ignored:\033[0m")
    print()
    print('\n'.join(ignored))
    print(separator)
