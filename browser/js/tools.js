/**
 * Find the position of the nth occurence of needle
 *
 * @param str string to analyze
 * @param needle char to find
 * @param nth but only the Nth occurence
 * @returns false of not found, or the position of the nth occurence.
 */
function nth_ocurrence(str, needle, nth) {
    for (i=0;i<str.length;i++) {
        if (str.charAt(i) == needle) {
            if (!--nth) {
                return i;
            }
        }
    }
    return false;
}

/**
 * transform a tab separated text into an associative js array
 *
 * @param allText
 * @returns {Array}
 */
function tsvToArray(allText) {
    var allTextLines = allText.split(/\r\n|\n/);
    var headers = allTextLines[0].split('	');
    var lines = [];

    for (var i = 1; i < allTextLines.length; i++) {
        var data = allTextLines[i].split('	');
        if (data.length == headers.length) {
            var tarr = {};
            for (var j = 0; j < headers.length; j++) {
                if (headers[j] != "") {
                    tarr[headers[j]] = data[j];
                }
            }
            lines.push(tarr);
        }
    }
    return lines;
}

/**
 * extract information from htlm page
 *
 * @param HTML code for a complete webpage
 */
function processImgtContents(IMGTresponse,tag) {

    var impl = document.implementation;
    //var htmlDoc = (new DOMParser).parseFromString(IMGTresponse, "text/html");
    var htmlDoc = document.implementation.createHTMLDocument("example");
    htmlDoc.documentElement.innerHTML= IMGTresponse;

    if (htmlDoc.length<10){
        console.log({
            "type": "log",
            "msg": "Error, Javascript engine does not supprt the parseFromString method..."});
    }
    var allpretext = ((htmlDoc.getElementsByTagName(tag))[0]).innerHTML;
    var idxFirst = allpretext.indexOf('Sequence number');
    var textlikecsv = allpretext.substr(idxFirst);
    var imgArray = tsvToArray(textlikecsv);
    return imgArray;
}

/**
 * Add start stop position for fields given in array according to
 * clone's sequence.
 * Used in IMGT/V-QUEST post-processing.
 *
 * @param seuence
 * @param arrayToProcess
 * @returns {object}
 */
function computeStartStop(arrayToProcess,sequence){

    var tpVal=0;
    var fldVal="";
    var result={};
    var junction = sequence;//arrayToProcess["JUNCTION"].toUpperCase();
    var junction_pos = 0; //sequence.indexOf(junction);

    var fields = [{field: "V-REGION", tooltip:arrayToProcess["V-GENE and allele"]},
                  {field: "J-REGION", tooltip:arrayToProcess["J-GENE and allele"]},
                  {field: "D-REGION", tooltip:arrayToProcess["D-GENE and allele"]},
                  {field: "CDR3-IMGT"}]

    var start;
    var stop;

    for (var i = 0; i < fields.length; i++) {
        start = -1;
        // Search using the sequence or just get the start and end positions?
        if (typeof arrayToProcess[fields[i].field+' start'] != 'undefined'
            && typeof arrayToProcess[fields[i].field+' end'] != 'undefined') {
            // IMGT positions start at 1
            start = arrayToProcess[fields[i].field+' start'] - 1;
            stop = arrayToProcess[fields[i].field+' end'] - 1;
        } else if (typeof arrayToProcess[fields[i].field] != 'undefined') {
            sequence_to_search = arrayToProcess[fields[i].field].toUpperCase();
            position = junction.indexOf(sequence_to_search);
            if (position > -1 && sequence_to_search.length > 0) {
                position += junction_pos;
                start = position;
                stop = position + sequence_to_search.length - 1;
            }
        }
        if (start != -1) {
            var tooltip = fields[i].tooltip
            if (typeof fields[i].tooltip == 'undefined') {
                tooltip = fields[i].field;
            }
            result[fields[i].field] = {seq: "", tooltip: tooltip, start: start, stop: stop };
        }
    }

    return result;
}

/**
 * Append (or overwrite) the data in array data into the array append_to.
 */
function append_to_object(data, append_to) {
    for (var key in data) {
        append_to[key] = data[key];
    }
}

/**
 * Give a nice decimal number above the given number
 * nice_ceil(0.14) -> 0.15
 * nice_ceil(23.4) -> 30
 **/

function nice_ceil(x)
{
    if (x <= 0) return x

    try {
        var floor_power10 = Math.pow(10,Math.floor(Math.log10(x)))

        var xx = x / floor_power10
        return (xx == 1 ? 1 : xx <= 1.5 ? 1.5 : Math.ceil(xx)) * floor_power10
    }
    catch(e) {
        // Always return something
        return x;
    }
}


/**
 * Give a nice decimal number under the given number
 * nice_floor(0.14) -> 0.1
 * nice_floor(23.4) -> 20
 **/

function nice_floor(x)
{
    if (x <= 0) return x

    try {
        var floor_power10 = Math.pow(10,Math.floor(Math.log10(x)))
        return Math.floor(x / floor_power10) * floor_power10
    }
    catch(e) {
        // Always return something
        return x;
    }
}
