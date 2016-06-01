# Valet 1.0 for AT&T Integrated Cloud (AIC) 3.5

## Installation Documentation

* qcow2 VM Image (valet-api, Ostro, Music, ostro-listener, HAValet): **Link TBD**.
* OpenStack Heat/Nova components (valet-openstack): Visit [http://valet.research.att.com/](http://valet.research.att.com/), select "valet-openstack".

## Downloads

* qcow2 VM Image (valet-api, Ostro, Music, ostro-listener, HAValet): **Link TBD**.
* OpenStack Heat/Nova components (valet-openstack): **Link TBD**.

## Solution Definition Template Updates

This section contains up-to-date changes for *AIC Valet Service Template Version 2.00* as of 26 May 2016, 9am EDT.

### Architecture

#### AIC Initiative/Feature Architecture Diagram

* Valet will plan all HEAT templates **containing nova servers**. It will not reject any template due to OpenStack features being used in the template.

#### External to AIC Platform - Document References

* RabbitMQ message broker **does not** require independent configuration
* URL: Can now use [http://valet.research.att.com/](http://valet.research.att.com/) (home page).

#### Summary of Activities to be taken up

* Figure 1, Step 2: Publish EG event to RO via Oslo Messaging Notification
* This resource type allows **the assignment** of exclusive groups of CSO Hypervisors (or Hosts).

#### New and impacted components for Development/Enhancement

* Valet 1.0 Components for KVM qcow2 image: Allegro is now Valet; Valet talks to Oslo Message Bus.
* Heat and Nova plugins: Combined in a single package, **valet-openstack**.
* Figure 3: Remove ``/%{tenant_id}s`` from valet-api publicurl, adminurl, and internalurl endpoints.
* AIC OpenStack Messaging; See subsection below.
* Placement API v1 Documentation: Visit [http://valet.research.att.com/](http://valet.research.att.com/), select "Placement API".

##### AIC OpenStack Messaging

Valet 1.0 syndicates all API requests/responses as Oslo Messaging Notifications.

The publisher name is “valet”, the topic name is “notifications”, and event types are all of the form “api.VERSION.SUBJECT” (e.g., “api.v1.groups”).

200-series responses are posted as INFO notifications. 400 and 500-series responses are posted as ERROR notifications. The notification payload is JSON and of this form:

```json
{
  "context": {
    "tenant_id": TENANT_ID,
    "user_id": USER_ID
  },
  "request": {
    "method": REQUEST_METHOD,
    "path": REQUEST_PATH,
    "body": REQUEST_BODY
  },
  "response": {
    "status_code": STATUS_CODE,
    "body": RESPONSE_BODY
  }
}
```

The request method identifies CRUD operations (POST: create, GET: read, etc.).

The Request and Response body is either a string (e.g., if an authentication error occurs, or an empty string if there is no request/response body) or JSON, as described in the Placement API documentation.

##### Valet 1.0 New Components

* Heat and Nova plugins are combined in a single package, **valet-openstack**. Proposed renaming: ``VALET_OPENSTACK_1.0.xxx.tar.gz``.
* Allegro has been renamed to Valet (e.g., Valet, valet-api, etc.).
* URL: Visit [http://valet.research.att.com/](http://valet.research.att.com/), select "Placement API".
* APIs for Tenant **membership in** Valet "Exclusive Group" 
* Heads-up example events: See earlier comment regarding AIC OpenStack Messaging.
* VM Migration Tip: See Placement API v1 Documentation, under "Update a plan" (PUT /v1/plans/{plan_id}) for example request and response.
* Placement API v1 Documentation: Visit [http://valet.research.att.com/](http://valet.research.att.com/), select "Placement API".

### Work Items - Details of Development/Enhancement

#### Provide Valet 1.0 qcow2 Image, Plugin, and Filter to AIC Image team

* Heat and Nova plugins: Combined in a single package, **valet-openstack**.

#### Provide Valet 1.0 Component Level Documentation to AIC Scrum teams

* All Valet Components: Visit [http://valet.research.att.com/](http://valet.research.att.com/) (home page).
* Heat Lifecycle and Nova Scheduler Filter plugin: Select "valet-openstack" from home page.
* RabbitMQ message broker **does not** require independent configuration
* Valet 1.0 Placement API v1 Documentation: Select "Placement API" from home page.

#### Upload Valet 1.0 Image and SW Files to target environments

* Heat and Nova plugins: Combined in a single package, **valet-openstack**.

#### eFORC Ordering - Provisionings for opening Valet 1.0 Ports and Firewall

* Ostro calls MUSIC APIs: APIs are not internal.
* All references to Allegro in "System Component" column are now "Valet".

#### Enhance Nagios Monitoring Scripts for Valet 1.0 + RO

* Nagios Health Check of Valet 1.0 service VIP: Can use Valet APIs. Use "GET /v1" for basic "ping" response (no AuthN required), or "HEAD /v1/status" for a round-trip check through Music and Ostro (requires valid Keystone token).

#### Spin-up 3 Valet 1.0 KVM VMs

* Valet calls OpenStack Keystone service and uses Oslo Message Bus.
* Valet is called by Heat and Nova via plugins from valet-openstack.

#### Configure vLCP HAPROXY for Valet 1.0 - PUBLIC_OAM and INTERNAL_MGMT

* Valet Service endpoint VIPs: Remove ``/%{tenant_id}s`` from valet-api publicurl, adminurl, and internalurl endpoints.

#### CSI-Middleware Impact and Creation of Valet service API endpoints

* Valet Service endpoint VIPs: Remove ``/%{tenant_id}s`` from valet-api publicurl, adminurl, and internalurl endpoints.

#### Configure Allegro and Ostro sub-systems on the Valet 1.0 VMs in AIC vLCP

* Note: Allegro is now called Valet.
* URL: Can now use [http://valet.research.att.com/](http://valet.research.att.com/) (home page).
* Allegro subsystem is now Valet subsystem. Components: valet-openstack and valet-api.
* OpenStack Configuration associated configurations in HEAT and NOVA: Documented in **valet-openstack**.
* Configurations: No rpc_cast associated configurations in AIC OpenStack Messaging system bus.

#### Configure HAValet and Music on the Valet 1.0 VMs in AIC vLCP for Fault Tolerance

* Valet 1.0 is replicated behind the AIC HAProxy - active-active replication **of valet-api**.
* HAValet monitors **valet-api**, Ostro, and the other HAValet processes...

#### Integration of Valet 1.0 software system into AIC 3.5

* RabbitMQ message broker **does not** require independent configuration
* Plugins, Filters, RabbitMQ Exchanges and Queues: See earlier comment regarding AIC OpenStack Messaging.
* Placement API v1 Documentation: Visit [http://valet.research.att.com/](http://valet.research.att.com/), select "Placement API".

#### Self Service Portal Impact - Valet 1.0 APIs

* URL: Can now use [http://valet.research.att.com/](http://valet.research.att.com/) (select "Placement API").
* VM Migration Tip: See Placement API v1 Documentation under "Update a plan" (PUT /v1/plans/{plan_id}) for example request and response.
* Placement API v1 Documentation: Visit [http://valet.research.att.com/](http://valet.research.att.com/), select "Placement API".

#### SO-Heat and Murano Impact - Valet 1.0 APIs

* URL: Can now use [http://valet.research.att.com/](http://valet.research.att.com/) (select "Placement API").
* VM Migration Tip: See Placement API v1 Documentation under "Update a plan" (PUT /v1/plans/{plan_id}) for example request and response.
* Placement API v1 Documentation: Visit [http://valet.research.att.com/](http://valet.research.att.com/), select "Placement API".

#### Validate Use Case Examples for Exclusivity

* ATT::Valet::GroupAssignment properties: ``name`` is now ``group_name``; ``relationship`` is now ``group_type``.

#### Validate Rainy day scenarios

* Item 5, "Either two or more of the Valet VMs are down...": Disregard cases a and b.

#### Validate Use Case Examples for Affinity, and Diversity (Anti-Affinity)

* ATT::Valet::GroupAssignment properties: ``relationship`` is now ``group_type``.
