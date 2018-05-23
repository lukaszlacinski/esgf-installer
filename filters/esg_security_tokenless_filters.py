
# Description: Installation of the esg-security infrastructure.  This
#              file is meant to be sourced by the esg-node | esg-gway
#              scripts that has the definition of checked_get(),
#              stop_tomcat(), start_tomcat(), $workdir,

service_name=${service_name:-"thredds"}
esg_root_dir=${esg_root_dir:-${ESGF_HOME:-"/esg"}}

esg_security_filters_dist_url=${esg_dist_url}/filters

esg_orp_version=${esg_orp_version:-"2.3.5"}
esgf_security_version=${esgf_security_version:-"2.3.15"}

def setup_security_tokenless_filters():
    esg_bash2py.mkdir_p(config["workdir"])
    with esg_bash2py.pushd(config["workdir"]):
        install_security_tokenless_filters()

#TODO: refactor
def insert_file_at_pattern(target_file, input_file, pattern):
    '''Replace a pattern inside the target file with the contents of the input file'''
    f=open(target_file)
    s=f.read()
    f.close()
    f=open(input_file)
    filter = f.read()
    f.close()
    s=s.replace(pattern,filter)
    f=open(target_file,'w')
    f.write(s)
    f.close()

def install_security_tokenless_filters(dest_dir="/usr/local/tomcat/webapps/thredds", esg_filter_entry_file="esg-access-logging-filter-web.xml"):

    service_name = esg_bash2py.trim_string_from_head(dest_dir)
    esg_filter_entry_pattern = "<!--@@esg_security_tokenless_filter_entry@@-->"

    print "*******************************"
    print "Installing Tomcat ESG SAML/ORP (Tokenless) Security Filters... for {}".format(service_name)
    print "-------------------------------"
    print "ESG ORP Filter: v{}".format(config["esg_orp_version"])
    print "ESGF Security (SAML): v${}".format(config["esgf_security_version"])
    print "*******************************"
    print "Filter installation destination dir = {}".format(dest_dir)
    print "Filter entry file = {}".format(esg_filter_entry_file)
    print "Filter entry pattern = {}".format(esg_filter_entry_pattern)

    #Installs esg filter into web application's web.xml file, by replacing a
    #place holder token with the contents of the filter snippet file
    #"esg-security-filter.xml".

    #pre-checking... make sure the files we need in ${service_name}'s dir are there....
    if not os.path.exists(os.path.join(dest_dir, "WEB-INF")):
        logger.error("WARNING: Could not find %s's installation dir - Filter Not Applied",service_name)
        return False
    if not os.path.exists(os.path.join(dest_dir, "WEB-INF", "lib")):
        logger.error("Could not find WEB-INF/lib installation dir - Filter Not Applied")
        return False
    if not os.path.exists(os.path.join(dest_dir, "WEB-INF", "lib")):
        logger.error("Could not find WEB-INF/lib installation dir - Filter Not Applied")
        return False
    if not os.path.exists(os.path.join(dest_dir, "WEB-INF", "web.xml")):
        logger.error("No web.xml file found for %s - Filter Not Applied", service_name)
        return False

    esg_tomcat_manager.stop_tomcat()

    get_orp_libs(os.path.join(dest_dir, "WEB-INF", "lib"))

    if not esg_filter_entry_pattern in open(os.path.join(dest_dir, "WEB-INF", "web.xml")).read():
        logger.info("No Pattern Found In File [%s/WEB-INF/web.xml] - skipping this filter setup\n", dest_dir)
        return

    with esg_bash2py.pushd(config["workdir"]):
        esg_dist_url = esg_property_manager.get_property("esg.dist.url")
        esg_security_filters_dist_url = "{}/filters".format(esg_dist_url)
        esg_functions.download_update("{}/{}".format(esg_security_filters_dist_url, esg_filter_entry_file))
        esg_filter_entry_file_path = esg_functions._readlinkf(esg_filter_entry_file)

    with esg_bash2py.pushd(os.path.join(dest_dir, "WEB-INF")):



#NOTE:This function will stop tomcat, it is up to the caller to restart tomcat!

#Takes 2 arguments:
# First  - The top level directory of the webapp where filter is to be installed.
# Second - The file containing the filter entry xml snippet (optional: defaulted)
install_security_tokenless_filters() {


    #Installs esg filter into web application's web.xml file, by replacing a
    #place holder token with the contents of the filter snippet file
    #"esg-security-filter.xml".

    #----------------------
    #Configuration...
    pushd ${dest_dir}/WEB-INF >& /dev/null
    [ $? != 0 ] && echo " ERROR: Could not find web application (${dest_dir})" && return 1
    local target_file=web.xml

    #Replace the filter's place holder token in web app's web.xml file with the filter entry.
    #Use utility function...
    insert_file_at_pattern $(readlink -f ${target_file}) ${esg_filter_entry_file} "${esg_filter_entry_pattern}"

    local orp_host=${orp_host:-${esgf_host}} #default assumes local install
    local authorization_service_root=${authorization_service_root:-${esgf_idp_peer}} #ex: pcmdi3.llnl.gov/esgcet[/saml/soap...]
    local truststore_file=${truststore_file:-"${tomcat_install_dir}/conf/jssecacerts"}
    local truststore_password=${truststore_password:-"changeit"}

    #Edit the web.xml file for the web app to include these token replacement values
    echo -n "Replacing tokens... "
    eval "perl -p -i -e 's#\\@orp_host\\@#${orp_host}#g' ${target_file}"; echo -n "*"
    eval "perl -p -i -e 's#\\@\\@#${truststore_file}#g' ${target_file}"; echo -n "*"
    eval "perl -p -i -e 's#\\@truststore_password\\@#${truststore_password}#g' ${target_file}"; echo -n "*"
    eval "perl -p -i -e 's#\\@esg_root_dir\\@#${esg_root_dir}#g' ${target_file}"; echo -n "*"
    echo " [OK]"
    popd >& /dev/null
    #----------------------


    chown -R ${tomcat_user} ${dest_dir}/WEB-INF
    chgrp -R ${tomcat_group} ${dest_dir}/WEB-INF
    echo "orp/security filters installed..."
    return 0
}

#Copies the filter jar file to the web app's lib dir
#arg 1 - The destination web application lib directory (default thredds)
get_orp_libs() {

    orp_service_app_home=${orp_service_app_home:-"${CATALINA_HOME}/webapps/esg-orp"}

    local dest_dir=${1:-${tomcat_install_dir}/webapps/${service_name}/WEB-INF/lib}
    local src_dir=${orp_service_app_home}/WEB-INF/lib

    #Jar versions...
    opensaml_version=${opensaml_version:-"2.3.2"}
    openws_version=${openws_version:-"1.3.1"}
    xmltooling_version=${xmltooling_version:-"1.2.2"}
    xsgroup_role_version=${xsgroup_role_version:-"1.0.0"}

    #(formerly known as endorsed jars)
    commons_collections_version=${commons_collections_version:-"3.2.2"}
    serializer_version=${serializer_version:-"2.9.1"}
    velocity_version=${velocity_version:-"1.5"}
    xalan_version=${xalan_version:-"2.7.2"}
    xercesImpl_version=${xercesImpl_version:-"2.10.0"}
    xml_apis_version=${xml_apis_version:-"1.4.01"}
    xmlsec_version=${xmlsec_version:-"1.4.2"}
    joda_version=${joda_version:-"2.0"}
    commons_io_version=${commons_io_version:-"2.4"}
    slf4j_version="1.6.4"

    #------------------------------------------------------------------
    #NOTE: Make sure that this version matches the version that is in
    #the esg-orp project!!!
    spring_version=${spring_version:-"4.2.3.RELEASE"}
    #------------------------------------------------------------------

    #----------------------------
    #Jar Libraries Needed To Be Present For ORP (tokenless) Filter Support
    #----------------------------
    opensaml_jar=opensaml-${opensaml_version}.jar
    openws_jar=openws-${openws_version}.jar
    xmltooling_jar=xmltooling-${xmltooling_version}.jar
    xsgroup_role_jar=XSGroupRole-${xsgroup_role_version}.jar

    #(formerly known as endorsed jars)
    commons_collections_jar=commons-collections-${commons_collections_version}.jar
    serializer_jar=serializer-${serializer_version}.jar
    velocity_jar=velocity-${velocity_version}.jar
    xalan_jar=xalan-${xalan_version}.jar
    xercesImpl_jar=xercesImpl-${xercesImpl_version}.jar
    xml_apis_jar=xml-apis-${xml_apis_version}.jar
    xmlsec_jar=xmlsec-${xmlsec_version}.jar
    joda_time_jar=joda-time-${joda_version}.jar
    commons_io_jar=commons-io-${commons_io_version}.jar
    slf4j_api_jar=slf4j-api-${slf4j_version}.jar
    slf4j_log4j_jar=slf4j-log4j12-${slf4j_version}.jar

    spring_jar=spring-core-${spring_version}.jar
    spring_web_jar=spring-web-${spring_version}.jar
    spring_webmvc_jar=spring-webmvc-${spring_version}.jar

    if [ -d ${dest_dir} ]; then
        #move over SAML libraries...
        echo "getting (copying) libary jars from the ORP to ${dest_dir}"

        [ ! -e ${dest_dir}/${opensaml_jar} ]     && cp -v ${src_dir}/${opensaml_jar}     ${dest_dir}
        [ ! -e ${dest_dir}/${openws_jar} ]       && cp -v ${src_dir}/${openws_jar}       ${dest_dir}
        [ ! -e ${dest_dir}/${xmltooling_jar} ]   && cp -v ${src_dir}/${xmltooling_jar}   ${dest_dir}
        [ ! -e ${dest_dir}/${xsgroup_role_jar} ] && cp -v ${src_dir}/${xsgroup_role_jar} ${dest_dir}

        #(formerly known as endorsed jars)
        [ ! -e ${dest_dir}/${commons_collections_jar} ] && cp -v ${src_dir}/${commons_collections_jar}  ${dest_dir}
        [ ! -e ${dest_dir}/${serializer_jar} ] && cp -v ${src_dir}/${serializer_jar} ${dest_dir}
        [ ! -e ${dest_dir}/${velocity_jar} ]   && cp -v ${src_dir}/${velocity_jar}   ${dest_dir}
        [ ! -e ${dest_dir}/${xalan_jar} ]      && cp -v ${src_dir}/${xalan_jar}      ${dest_dir}
        [ ! -e ${dest_dir}/${xercesImpl_jar} ] && cp -v ${src_dir}/${xercesImpl_jar} ${dest_dir}
        [ ! -e ${dest_dir}/${xml_apis_jar} ]   && cp -v ${src_dir}/${xml_apis_jar}   ${dest_dir}
        [ ! -e ${dest_dir}/${xmlsec_jar} ]     && cp -v ${src_dir}/${xmlsec_jar}     ${dest_dir}
        [ ! -e ${dest_dir}/${joda_time_jar} ]  && cp -v ${src_dir}/${joda_time_jar}  ${dest_dir}
        [ ! -e ${dest_dir}/${commons_io_jar} ] && cp -v ${src_dir}/${commons_io_jar}  ${dest_dir}
        [ ! -e ${dest_dir}/${slf4j_api_jar} ]  && cp -v ${src_dir}/${slf4j_api_jar}  ${dest_dir}
        [ ! -e ${dest_dir}/${slf4j_log4j12_jar} ] && cp -v ${src_dir}/${slf4j_log4j12_jar} ${dest_dir}

        #----------------------------
        #Fetching ORP / Security Jars from Distribution Site...
        #----------------------------

        #values inherited from esg-node calling script
        #-----
        #project generated jarfiles...
        local esg_orp_jar=esg-orp-${esg_orp_version}.jar
        local esgf_security_jar=esgf-security-${esgf_security_version}.jar
        #-----

        echo "getting (downloading) library jars from ESGF Distribution Server (ORP/Security) to ${dest_dir} ..."
        local make_backup_file=0 #Do NOT make backup file

		if [ "$service_name" = "las" ]; then
        #Trying to avoid going on the wire to fetch files... see if the ORP has it locally first.
        if [[ ! -e "${dest_dir}/${spring_jar}" ]]; then
            if [[ -e "${src_dir}/${spring_jar}" ]]; then
                cp -v ${src_dir}/${spring_jar} ${dest_dir}/${spring_jar}
            else
                checked_get ${dest_dir}/${spring_jar} ${esg_dist_url}/filters/${spring_jar} $((force_install)) $((make_backup_file))
            fi
        else
            ((DEBUG)) && echo "${dest_dir}/${spring_jar} - [OK]"
        fi

        if [[ ! -e "${dest_dir}/${spring_webmvc_jar}" ]]; then
            if [[ -e "${src_dir}/${spring_webmvc_jar}" ]]; then
                cp -v ${src_dir}/${spring_webmvc_jar} ${dest_dir}/${spring_webmvc_jar}
            else
                checked_get ${dest_dir}/${spring_webmvc_jar} ${esg_dist_url}/filters/${spring_webmvc_jar} $((force_install)) $((make_backup_file))
            fi
        else
            ((DEBUG)) && echo "${dest_dir}/${spring_webmvc_jar} - [OK]"
        fi

        if [[ ! -e "${dest_dir}/${spring_web_jar}" ]]; then
            if [[ -e "${src_dir}/${spring_web_jar}" ]]; then
                cp -v ${src_dir}/${spring_web_jar} ${dest_dir}/${spring_web_jar}
            else
                checked_get ${dest_dir}/${spring_web_jar} ${esg_dist_url}/filters/${spring_web_jar} $((force_install)) $((make_backup_file))
            fi
        else
            ((DEBUG)) && echo "${dest_dir}/${spring_web_jar} - [OK]"
        fi

		fi #end of las-only block for the spring jars.

        if [[ ! -e "${dest_dir}/${esgf_security_jar}" ]]; then
            if [[ -e "${src_dir}/${esgf_security_jar}" ]]; then
                cp -v ${src_dir}/${esgf_security_jar} ${dest_dir}/${esgf_security_jar}
            else
                checked_get ${dest_dir}/${esgf_security_jar} ${esg_dist_url}/esgf-security/${esgf_security_jar} $((force_install)) $((make_backup_file))
            fi
        else
            ((DEBUG)) && echo "${dest_dir}/${esgf_security_jar} - [OK]"
        fi

        if [[ ! -e "${dest_dir}/${esg_orp_jar}" ]]; then
            checked_get ${dest_dir}/${esg_orp_jar} ${esg_dist_url}/esg-orp/${esg_orp_jar} $((force_install)) $((make_backup_file))
        fi


        #remove all other orp / security jar versions that we don't want
        echo "cleaning up (removing) other, unnecessary, orp/security project jars from ${dest_dir} ..."
        rm -vf $(/bin/ls ${dest_dir}/${esg_orp_jar%-*}-*.jar | grep -v ${esg_orp_version})
        rm -vf $(/bin/ls ${dest_dir}/${esgf_security_jar%-*}-*.jar | grep -v ${esgf_security_version})
        #---

        chown -R ${tomcat_user}:${tomcat_group} ${dest_dir}
    fi

}
