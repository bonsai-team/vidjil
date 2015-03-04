# coding: utf8
import gluon.contrib.simplejson
if request.env.http_origin:
    response.headers['Access-Control-Allow-Origin'] = request.env.http_origin  
    response.headers['Access-Control-Allow-Credentials'] = 'true'
    response.headers['Access-Control-Max-Age'] = 86400

def index():
    if not auth.user : 
        res = {"redirect" : "default/user/login"}
        return gluon.contrib.simplejson.dumps(res, separators=(',',':'))
    

    query = db((auth.accessible_query('read', db.config) | auth.accessible_query('admin', db.config) ) ).select() 

    return dict(message=T('Configs'),
               query=query,
               isAdmin = auth.has_membership("admin"))


def add(): 
    return dict(message=T('Add config'))


#TODO check data
def add_form(): 
    error =""

    required_fields = ['config_name', 'config_command', 'config_fuse_command', 'config_program']
    for field in required_fields:
        if request.vars[field] == "" :
            error += field+" needed, "

    if error=="" :
        
        db.config.insert(name=request.vars['config_name'],
                        info=request.vars['config_info'],
                        command=request.vars['config_command'],
                        fuse_command=request.vars['config_fuse_command'],
                        program=request.vars['config_program']
                        )

        res = {"redirect": "config/index",
               "message": "config added"}
        return gluon.contrib.simplejson.dumps(res, separators=(',',':'))
        
    else :
        res = {"success" : "false", "message" : error}
        return gluon.contrib.simplejson.dumps(res, separators=(',',':'))


def edit(): 
    return dict(message=T('edit config'))


def edit_form(): 
    import shutil, os.path
    
    error =""

    required_fields = ['id', 'config_name', 'config_command', 'config_fuse_command', 'config_program']
    for field in required_fields:
        if request.vars[field] == "" :
            error += field+" needed, "

    if error=="" :

        db.config[request.vars["id"]] = dict(name=request.vars['config_name'],
                                             info=request.vars['config_info'],
                                             command=request.vars['config_command'],
                                             fuse_command=request.vars['config_fuse_command'],
                                             program=request.vars['config_program']
                                             )

        res = {"redirect": "config/index",
               "message": "config saved"}

        log.info(res)
        return gluon.contrib.simplejson.dumps(res, separators=(',',':'))

    else :
        res = {"success" : "false", "message" : error}
        log.error(res)
        return gluon.contrib.simplejson.dumps(res, separators=(',',':'))

def confirm():
    return dict(message=T('confirm config deletion'))

def delete():
    import shutil, os.path
    
    #delete results_file using this config
    db(db.results_file.config_id==request.vars["id"]).delete()
    
    #delete config
    db(db.config.id==request.vars["id"]).delete() 
    
    res = {"redirect": "config/index",
           "message": "config deleted"}
    return gluon.contrib.simplejson.dumps(res, separators=(',',':'))


def permission(): 
    if (auth.has_permission('admin', 'patient', request.vars["id"]) ):
        
        query = db( db.auth_group.role != 'admin' ).select()
        
        for row in query :
            row.owner = row.role
            if row.owner[:5] == "user_" :
                id = int(row.owner[5:])
                row.owner = db.auth_user[id].first_name + " " + db.auth_user[id].last_name 

            row.admin = False
            if db(   (db.auth_permission.name == "admin")
                  & (db.auth_permission.record_id == request.vars["id"])
                  & (db.auth_permission.group_id == row.id)
                  & (db.auth_permission.table_name == db.config)
              ).count() > 0 :
                row.admin = True
                
            row.read = False
            if db(   (db.auth_permission.name == "read")
                  & (db.auth_permission.record_id == request.vars["id"])
                  & (db.auth_permission.group_id == row.id)
                  & (db.auth_permission.table_name == db.config)
              ).count() > 0 :
                row.read = True
        
        return dict(query = query)
    else :
        res = {"message": ACCESS_DENIED}
        log.error(res)
        return gluon.contrib.simplejson.dumps(res, separators=(',',':'))
    
#TODO refactor with patient/change_permission
def change_permission():
    if (auth.has_permission('admin', 'config', request.vars["config_id"]) ):
        error = ""
        if request.vars["group_id"] == "" :
            error += "missing group_id, "
        if request.vars["config_id"] == "" :
            error += "missing patient_id, "
        if request.vars["permission"] == "" :
            error += "missing permission, "

        if error=="":
            if db(   (db.auth_permission.name == request.vars["permission"])
                      & (db.auth_permission.record_id == request.vars["config_id"])
                      & (db.auth_permission.group_id == request.vars["group_id"])
                      & (db.auth_permission.table_name == db.config)
                  ).count() > 0 :
                auth.del_permission(request.vars["group_id"], request.vars["permission"], db.config, request.vars["config_id"])
                res = {"message" : "access '%s' deleted to '%s'" % (request.vars["permission"], db.auth_group[request.vars["group_id"]].role)}
            else :
                auth.add_permission(request.vars["group_id"], request.vars["permission"], db.config, request.vars["config_id"])
                res = {"message" : "access '%s' granted to '%s'" % (request.vars["permission"], db.auth_group[request.vars["group_id"]].role)}
            
            log.info(res)
            return gluon.contrib.simplejson.dumps(res, separators=(',',':'))
        else :
            res = {"message": "incomplete request : "+error }
            log.error(res)
            return gluon.contrib.simplejson.dumps(res, separators=(',',':'))
    else :
        res = {"message": ACCESS_DENIED}
        log.error(res)
        return gluon.contrib.simplejson.dumps(res, separators=(',',':'))
