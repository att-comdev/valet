*Note: These instructions are specific to the CloudQoS environment.*

Greetings, intrepid CloudQoS explorers!

The following examples are provided for use with ATT::QoS Heat resources on the agave OpenStack cluster:

* **simple**: A simple two server deployment.
* **wordpress**: Everyone's favorite blogging platform, QoS-i-fied.
* **qosdeploy**: Deployment from outside of Heat *without* ATT::QoS::DeploymentGroup.

There are two prerequisites that must be met before you can try them out. These prerequisites use the agave OpenStack cluster (login required).

First, you will need to create a Key Pair named "demo":

```
http://agave101.research.att.com/horizon/project/access_and_security/
```

A private key will download automatically. Keep it in a safe place! You will have the opportunity to use it later on in these instructions.

Second, you will need to download and source in your OpenStack RC file:

```
http://agave101.research.att.com/horizon/project/access_and_security/api_access/openrc/
```

Source this file from the command line of your agave101 account like so:

```bash
$ . path/to/your/openrc.sh
```

You will be asked for your OpenStack password *once* (no verification). If you suspect the password was typed incorrectly, just source it again.

To try these examples out, just cd into the directory and create the stack:

```bash
$ cd simple
$ heat stack-create dg --template-file simple_dg.template
```

or:

```bash
$ cd wordpress
$ heat stack-create dg --template-file wordpress_dg.template
```

dg is the name of the stack (it can be anything, really).

For qosdeploy, use:

```bash
$ cd qosdeploy
$ qosdeploy stack-create test --template-file test.yaml
```

To try a qosdeploy update, use:

```bash
$ qosdeploy stack-update test --template-file update.yaml
```

To view a list of stacks and their status:

```bash
$ heat stack-list
```

To show a specific stack (let's say the dg stack we just created):

```bash
$ heat stack-show dg
```

Once your stack shows a stack_status of CREATE_COMPLETE, use stack-show to get the public-facing IP address of each server. You can ssh to it like so:

```bash
$ ssh -i demo.pem fedora@YOUR_IP_ADDRESS
```

The "fedora" account is set up as part of the Fedora disk image used in these examples. It also comes with sudo privileges.

To delete a stack (again, using dg as the example):

```bash
$ heat stack-delete dg
```

This can be done with qosdeploy as well:

```bash
$ qosdeploy stack-delete test
```

More info:

```
https://forge.research.att.com/plugins/mediawiki/wiki/qoscloud/index.php/Main_Page#Orchestration
```

Updated: 10 October 2014
Contact: <jdandrea@research.att.com>
