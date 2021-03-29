from rest_framework import serializers
from gkutils.commonutils import coneSearchHTM, FULL, QUICK, CAT_ID_RA_DEC_COLS, base26, Struct
from datetime import datetime
from django.db import connection
from django.db import IntegrityError
import lasair.settings
import requests
import json
import re
import fastavro
import datetime

def record_user(userId, service):
    f = open('/home/ubuntu/lasair-lsst-web/src/lasair-webapp/lasair/static/api_users.txt', 'a')
    now_number = datetime.datetime.utcnow()
    utc = now_number.strftime("%Y-%m-%d %H:%M:%S")
    s = '%s, %s, %s\n' % (utc, userId, service)
    f.write(s)
    f.close()

CAT_ID_RA_DEC_COLS['objects'] = [['objectId', 'ramean', 'decmean'],1018]

REQUEST_TYPE_CHOICES = (
        ('count', 'Count'),
        ('all', 'All'),
        ('nearest', 'Nearest'),
    )

class ConeSerializer(serializers.Serializer):
    ra          = serializers.FloatField(required=True)
    dec         = serializers.FloatField(required=True)
    radius      = serializers.FloatField(required=True)
    requestType = serializers.ChoiceField(choices=REQUEST_TYPE_CHOICES)

    def save(self):

        ra          = self.validated_data['ra']
        dec         = self.validated_data['dec']
        radius      = self.validated_data['radius']
        requestType = self.validated_data['requestType']

        # Get the authenticated user, if it exists.
        userId = 'unknown'
        request = self.context.get("request")
        if request and hasattr(request, "user"):
            userId = request.user
            record_user(userId, 'cone')

        if radius > 1000:
            replyMessage = "Max radius is 1000 arcsec."
            info = { "error": replyMessage }
            return info

        replyMessage = 'No object found ra=%.5f dec=%.5f radius=%.2f' % (ra, dec, radius)
        info = {"error": replyMessage}

        # Is there an object within RADIUS arcsec of this object? - KWS - need to fix the gkhtm code!!
        message, results = coneSearchHTM(ra, dec, radius, 'objects', queryType = QUICK, conn = connection, django = True, prefix='htm', suffix = '')

        obj = None
        separation = None

        objectList = []
        if len(results) > 0:
            if requestType == "nearest":
                obj = results[0][1]['objectId']
                separation = results[0][0]
                info = { "object": obj, "separation": separation }
            elif requestType == "all":
                for row in results:
                    objectList.append({"object": row[1]["objectId"], "separation": row[0]})
                info = objectList
            elif requestType == "count":
                info = {'count': len(results)}
            else:
                info = { "error": "Invalid request type" }

        return info

from lasair.objects import objjson
class ObjectsSerializer(serializers.Serializer):
    objectIds = serializers.CharField(required=True)

    def save(self):
        objectIds = self.validated_data['objectIds']

        olist = []
        for tok in objectIds.split(','):
            olist.append(tok.strip())
        olist = olist[:10] # restrict to 10

        # Get the authenticated user, if it exists.
        userId = 'unknown'
        request = self.context.get("request")
        if request and hasattr(request, "user"):
            userId = request.user
            record_user(userId, 'object')

        result = []  
        for objectId in olist:
            result.append(objjson(objectId))
        return result

class SherlockObjectsSerializer(serializers.Serializer):
    objectIds = serializers.CharField(required=True)
    lite      = serializers.BooleanField()

    def save(self):
        objectIds = None
        lite = False
        objectIds = self.validated_data['objectIds']

        if 'lite' in self.validated_data:
            lite      = self.validated_data['lite']

        # Get the authenticated user, if it exists.
        userId = 'unknown'
        request = self.context.get("request")
        if request and hasattr(request, "user"):
            userId = request.user
            record_user(userId, 'sherlockobjects')

        datadict = {}
        url = 'http://%s/object/%s' % (lasair.settings.SHERLOCK_SERVICE, objectIds)
        if lite: url += '?lite=true'
        r = requests.get(url)
        if r.status_code == 200:
            return r.json()
        else: 
            return {"error": r.text}

class SherlockPositionSerializer(serializers.Serializer):
    ra        = serializers.FloatField(required=True)
    dec       = serializers.FloatField(required=True)
    lite      = serializers.BooleanField()

    def save(self):
        lite = False
        ra        = self.validated_data['ra']
        dec       = self.validated_data['dec']
        if 'lite' in self.validated_data:
            lite      = self.validated_data['lite']

        # Get the authenticated user, if it exists.
        userId = 'unknown'
        request = self.context.get("request")
        if request and hasattr(request, "user"):
            userId = request.user
            record_user(userId, 'sherlockposition')
# can also send multiples, but not yet implemented
# http://192.41.108.29/query?ra=115.811388,97.486925&dec=-25.76404,-26.975506

        url = 'http://%s/query?ra=%f&dec=%f' % (lasair.settings.SHERLOCK_SERVICE, ra, dec)
        if lite: url += '&lite=true'
        r = requests.get(url)
        if r.status_code != 200:
            return {"error":  r.text}
        else:
            return json.loads(r.text)

from utility import query_utilities
import mysql.connector

def connect_db():
    msl = mysql.connector.connect(
        user    =lasair.settings.READONLY_USER,
        password=lasair.settings.READONLY_PASS,
        host    =lasair.settings.DATABASES['default']['HOST'],
        database='ztf')
    return msl

class QuerySerializer(serializers.Serializer):
    selected   = serializers.CharField(max_length=4096, required=True)
    tables     = serializers.CharField(max_length=1024, required=True)
    conditions = serializers.CharField(max_length=4096, required=True)
    limit      = serializers.IntegerField(max_value=1000000, required=False)
    offset     = serializers.IntegerField(required=False)

    def save(self):
        selected   = self.validated_data['selected']
        tables     = self.validated_data['tables']
        conditions = self.validated_data['conditions']
        limit = None
        if 'limit' in self.validated_data:
            limit      = self.validated_data['limit']
        offset = None
        if 'offset' in self.validated_data:
            offset     = self.validated_data['offset']

        # Get the authenticated user, if it exists.
        userId = 'unknown'
        request = self.context.get("request")
        maxlimit = 1000
        if request and hasattr(request, "user"):
            userId = request.user
            if str(userId) != 'dummy':
                maxlimit = 10000
            for g in request.user.groups.all():
                if g.name == 'powerapi':
                    maxlimit = 1000000
            record_user(userId, 'query')

        page = 0
        limitseconds = 300

        if limit == None: limit = 1000
        else:             limit = int(limit)
        limit = min(maxlimit, limit)

        if offset == None: offset = 0
        else:              offset = int(offset)

        if 'limit' in conditions.lower():
            error = 'Do not put LIMIT in your SQL, use the query parameter instead'
            return {"error":error}

        sqlquery_real = query_utilities.make_query(selected, tables, conditions, limit, offset, limitseconds)
        msl = connect_db()
        cursor = msl.cursor(buffered=True, dictionary=True)
        result = []
        try:
            cursor.execute(sqlquery_real)
            for row in cursor: result.append(row)
            return result
        except Exception as e:
            error = 'Your query:<br/><b>' + sqlquery_real + '</b><br/>returned the error<br/><i>' + str(e) + '</i>'
            return {"error":error}

class StreamsSerializer(serializers.Serializer):
    topic = serializers.SlugField(required=False)
    limit   = serializers.IntegerField(required=False)
    regex = serializers.CharField(required=False)

    def save(self):
        topic = None
        if 'topic' in self.validated_data:
            topic = self.validated_data['topic']

        limit = None
        if 'limit' in self.validated_data:
            limit = self.validated_data['limit']

        regex = None
        if 'regex' in self.validated_data:
            regex = self.validated_data['regex']

        if not topic and not regex:
            regex = '.*'

        # Get the authenticated user, if it exists.
        userId = 'unknown'
        request = self.context.get("request")
        if request and hasattr(request, "user"):
            userId = request.user
            record_user(userId, 'streams')

        if topic:
            if 1:
                datafile = open(lasair.settings.BLOB_STORE_ROOT + '/streams/%s' % topic, 'r').read()
                data = json.loads(datafile)['digest']
                if limit: data = data[:limit]
                return data
            else:
                return []

        if regex:
            try:
                r = re.compile(regex)
            except:
                replyMessage = '%s is not a regular expression' % regex
                return { "topics": [], "info": replyMessage }

            msl = connect_db()
            cursor = msl.cursor(buffered=True, dictionary=True)
            result = []
            query = 'SELECT mq_id, user, name FROM myqueries WHERE active>0'
            cursor.execute(query)
            for row in cursor: 
                tn = query_utilities.topic_name(row['user'], row['name'])
                if r.match(tn):
                    td = {'topic':tn, 'more_info':'https://lasair-iris.roe.ac.uk/query/%d/' % row['mq_id']}
                    result.append(td)
            info = result
            return info

        return { "error": 'Must supply either topic or regex' }

def get_lightcurve(objectId):
    json_store = objectStore(suffix = 'json',
        fileroot=lasair.settings.BLOB_STORE_ROOT + '/objectjson')

    json_object = json_store.getObject(objectId)
    if not json_object or len(json_object) == 0:
        message = 'objectId %s does not exist'%objectId
        return {"error":message}
    candidates = json.loads(json_object)
    return candidates

def get_lightcurves(objectIds):
    ncand = 0
    lightcurves = []
    for objectId in objectIds:
        lightcurves.append(get_lightcurve(objectId))
    return lightcurves

from utility.objectStore import objectStore
class LightcurvesSerializer(serializers.Serializer):
    objectIds = serializers.CharField(max_length=16384, required=True)
    def save(self):
        objectIds = self.validated_data['objectIds']
        olist = []
        for tok in objectIds.split(','):
            olist.append(tok.strip())

        # Get the authenticated user, if it exists.
        userId = 'unknown'
        request = self.context.get("request")
        if request and hasattr(request, "user"):
            userId = request.user
            record_user(userId, 'lightcurves')

        lightcurves = get_lightcurves(olist)
        return lightcurves
