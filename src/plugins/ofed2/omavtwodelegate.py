import eisoil.core.pluginmanager as pm
import eisoil.core.log
import copy
logger=eisoil.core.log.getLogger('ofed')

GMAv2DelegateBase = pm.getService('gmav2delegatebase')
gfed_ex = pm.getService('apiexceptionsv2')

VERSION = '2'

class OMAv2Delegate(GMAv2DelegateBase):
    """
    Implements Member Authority methods.

    Does validity checking on passed options.
    """

    def __init__(self):
        """
        Get plugins for use in other class methods.

        Retrieve whitelists for use in validity checking.
        """
        self._member_authority_resource_manager = pm.getService('omemberauthorityrm')
        self._delegate_tools = pm.getService('delegatetools')
        self._member_whitelist = self._delegate_tools.get_whitelist('MEMBER')
        self._key_whitelist = self._delegate_tools.get_whitelist('KEY')
        self._logging_authority_resource_manager = pm.getService('ologgingauthorityrm')
        self._gmav2handler = pm.getService('gmav2handler')

    def get_version(self):
        """
        Get implementation details from resource manager. Supplement these with
        additional details specific to the delegate.
        """
        version = self._delegate_tools.get_version(self._member_authority_resource_manager)
        version['VERSION'] = VERSION
        # version['FIELDS'] = self._delegate_tools.get_supplementary_fields(['MEMBER', 'KEY'])
        return version

    def create(self, type_, credentials, fields, options):
        """
        Depending on the object type defined in the request, check the validity
        of passed fields for a 'create' call; if valid, create this object using
        the resource manager.
        """
        fields_copy = copy.copy(fields) if fields else None
        client_ssl_cert = self._gmav2handler.requestCertificate()

        if (type_.upper()=='KEY'):
            # Authorization
            self._delegate_tools.check_if_authorized(credentials, client_ssl_cert, 'CREATE', 'KEY', None, fields)
            # Consistency checks
            self._delegate_tools.object_creation_check(fields, self._key_whitelist)
            self._delegate_tools.object_consistency_check(type_, fields)
            # Creation
            ret_values =  self._member_authority_resource_manager.create_key(credentials, fields, options)
            # Logging
            key_member = fields_copy['KEY_MEMBER'] if 'KEY_MEMBER' in fields_copy.keys() else None
            self._logging_authority_resource_manager.append_event_log(authority='ma', method='create', target_type=type_.upper(),
                    fields=None, options= None, target_urn=ret_values['KEY_ID'], credentials=credentials)
            return ret_values

        elif (type_.upper() =='MEMBER'):
            # Authorization
            self._delegate_tools.check_if_authorized(credentials, client_ssl_cert, 'CREATE', 'SYSTEM_MEMBER')
            # Consistency checks
            self._delegate_tools.object_creation_check(fields, self._member_whitelist)
            self._delegate_tools.object_consistency_check(type_, fields)
            # Registration
            ret_values = self._member_authority_resource_manager.register_member(credentials, fields, options)
            # Logging
            user_name = fields_copy['MEMBER_USERNAME'] if 'MEMBER_USERNAME' in fields_copy.keys() else None
            user_urn = ret_values['MEMBER_URN'] if 'MEMBER_URN' in ret_values.keys() else None
            self._logging_authority_resource_manager.append_event_log(authority='ma', method='create', target_type=type_.upper(),
                    fields={'MEMBER_USERNAME':user_name}, options= None, target_urn=user_urn, credentials=credentials)
            return ret_values

        else:
            raise gfed_ex.GFedv2NotImplementedError("No create method found for object type: " + str(type_))

    def update(self, type_, urn, credentials, fields, options):
        """
        Depending on the object type defined in the request, check the validity
        of passed fields for a 'update' call; if valid, update this object using
        the resource manager.
        """
        fields_copy = copy.copy(fields) if fields else None
        options_copy = copy.copy(options) if options else None
        client_ssl_cert = self._gmav2handler.requestCertificate()

        if (type_.upper()=='MEMBER'):
            # Authorization
            self._delegate_tools.check_if_ma_info_update_authorized(credentials, client_ssl_cert, 'SYSTEM_MEMBER', urn)
            # Consistency checks
            self._delegate_tools.object_update_check(fields, self._member_whitelist)
            self._delegate_tools.object_consistency_check(type_, fields)
            # Update
            ret_values = self._member_authority_resource_manager.update_member(urn, credentials, fields, options)
            # Logging
            self._logging_authority_resource_manager.append_event_log(authority='ma', method='Renew' if 'MEMBER_CERTIFICATE' in fields.keys() else 'update', target_type=type_.upper(),
                    fields=fields_copy, options= options_copy, target_urn=urn, credentials=credentials)
            return ret_values

        elif (type_.upper()=='KEY'):
            # Authorization
            self._delegate_tools.check_if_ma_info_update_authorized(credentials, client_ssl_cert,  type_, urn)
            # Consistency checks
            self._delegate_tools.object_update_check(fields, self._key_whitelist)
            self._delegate_tools.object_consistency_check(type_, fields)
            # Update
            ret_values = self._member_authority_resource_manager.update_key(urn, credentials, fields, options)
            # Logging
            self._logging_authority_resource_manager.append_event_log(authority='ma', method='update', target_type=type_.upper(),
                    fields=fields_copy, options= options_copy, target_urn=urn, credentials=credentials)
            return ret_values

        else:
            raise gfed_ex.GFedv2NotImplementedError("No update method found for object type: " + str(type_))

    def delete(self, type_, urn, credentials, options):
        """
        Depending on the object type defined in the request, delete this object
        using the resource manager.
        """
        options_copy = copy.copy(options) if options else None
        client_ssl_cert = self._gmav2handler.requestCertificate()

        if (type_.upper()=='KEY'):
            # Authorization
            self._delegate_tools.check_if_ma_info_update_authorized(credentials, client_ssl_cert, type_, urn)
            # Removal
            ret_values = self._member_authority_resource_manager.delete_key(urn, credentials, options)
            # Logging
            self._logging_authority_resource_manager.append_event_log(authority='ma', method='delete', target_type=type_.upper(),
                    fields=None, options= options_copy, target_urn=urn, credentials=credentials)
            return ret_values
        else:
            raise gfed_ex.GFedv2NotImplementedError("No delete method found for object type: " + str(type_))

    def lookup(self, type_, credentials, match, filter_, options):
        """
        Depending on the object type defined in the request, lookup this object
        using the resource manager.
        """
        # Turn off logging for lookups
        # options_copy = copy.copy(options) if options else None

        if type_.upper() == 'MEMBER':
            # Consistency checks
            self._delegate_tools.object_lookup_check(match, self._member_whitelist)
            self._delegate_tools.object_consistency_check(type_, match)

            # Authorization
            # self._delegate_tools.check_if_authorized(credentials, 'LOOKUP', 'SYSTEM_MEMBER')
            remove_anchor_key = False
            if filter_ and 'MEMBER_URN' not in filter_:
                filter_.append('MEMBER_URN')
                remove_anchor_key = True

            match_urn_list = self._delegate_tools.decompose_urns(match, 'MEMBER_URN')

            # Lookup
            result_list = []
            for urn in match_urn_list:
                result_list = result_list+self._member_authority_resource_manager.lookup_member(credentials, urn, [] if filter_ is None else filter_, options)

            ret_values = self._delegate_tools.to_keyed_dict(result_list, "MEMBER_URN", filter_, remove_anchor_key)
            # self._logging_authority_resource_manager.append_event_log(authority='ma', method='lookup', target_type=type_.upper(),
            #         fields=None, options= options_copy, credentials=credentials)
            return ret_values

        elif (type_.upper()=='KEY'):
            # Authorization
            #self._delegate_tools.check_if_authorized(credentials, 'LOOKUP', 'KEY')
            remove_anchor_key = False
            if filter_ and 'KEY_ID' not in filter_:
                filter_.append('KEY_ID')
                remove_anchor_key = True
            # Lookup
            ret_values = self._delegate_tools.to_keyed_dict(self._member_authority_resource_manager.lookup_key(
                credentials, match, [] if filter_ is None else filter_, options), "KEY_ID", filter_, remove_anchor_key)
            # self._logging_authority_resource_manager.append_event_log(authority='ma', method='lookup', target_type=type_.upper(),
            #         fields=None, options= options_copy, credentials=credentials)
            return ret_values

        else:
            raise gfed_ex.GFedv2NotImplementedError("No lookup method found for object type: " + str(type_))

    def verify_certificate(self, cert_to_verify, credentials):
        """
        Verifies if given certificate is valid and trusted
        """
        return self._delegate_tools.verify_certificate(cert_to_verify)

    def get_crl(self, credentials):
        """
        Generates an updated CRL in PEM format
        :param credentials:
        :return:
        """
        return self._member_authority_resource_manager.generate_crl()

    def get_credentials(self, member_urn, credentials, options):
        """
        Provide list of credentials (signed statements) for given member
        This is member-specific information suitable for passing as credentials in
         an AM API call for aggregate authorization.
        Arguments:
           member_urn: URN of member for which to retrieve credentials
           options: Potentially contains 'speaking_for' key indicating a speaks-for
               invocation (with certificate of the accountable member in the credentials argument)

        Return:
            List of credential in 'CREDENTIALS' format, i.e. a list of credentials with
               type information suitable for passing to aggregates speaking AM API V3.
        """
        return self._member_authority_resource_manager.get_credentials(member_urn, credentials, options)

    def revoke(self, member_urn, credentials):
        """
        Revokes a member certificate.
        Arguments:
           member_urn: URN of member whose certificate is to be revoked
        Return:
           None
        """
        self._logging_authority_resource_manager.append_event_log(authority='ma', method='Revoke certificate', target_type='MEMBER',
                    fields=None, options=None, target_urn=member_urn, credentials=credentials)

        return self._member_authority_resource_manager.revoke_certificate(member_urn)

    def assign_privileges(self, member_urn, credentials, privileges):
        """
        Assigns given privileges to a system member
        :param member_urn: URN of member
        :param credentials: Actor's credentials usually root
        :param privileges_list: list of privileges to be assigned
        :return: Updated member credential
        """
        self._logging_authority_resource_manager.append_event_log(authority='ma', method='Assign privileges', target_type='MEMBER',
                    fields=privileges, options=None, target_urn=member_urn, credentials=credentials)

        return self._member_authority_resource_manager.assign_privileges(member_urn, credentials, privileges)