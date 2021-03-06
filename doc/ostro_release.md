Valet1.0/Ostro features

-   Optimal VM placement Use the decent algorithm, compute the holistic
    optimal placement for all VMs of given application. Working on
    NUMAAffinityFilter and PCIPassthroughFilter.

-   Constraint solving (filtering) Current constraints (i.e., filters)
    include CoreFilter, RamFilter, DiskFilter, host aggregates,
    availability zones. Possibly, the decision making of Ostro is
    different from Nova when tenant attempts to use other filters
    available in Nova. In this case, Ostro yields its decision to Nova
    scheduler unless the tenant uses affinity, diversity, and
    exclusivity in Heat template. However, we will restrict some Nova
    filters if it affects cloud security, reliability, and efficiency.

-   Affinity, Diversity, and Exclusivity in either host or rack level In
    addition of the above filters, support affinity, diversity
    (anti-affinity), and exclusivity. The rack level can be supported
    when the topology/layout information of site is available.
    Currently, use the host machine naming convention. If a site does
    not follow the naming convention, the rack level request will be
    rejected. Note that you can use the mix of these special filters and
    the basic filters.

-   Resource standby When allocating resources (CPU, memory, disk, and
    later network bandwidth), Ostro intentionally leaves a certain
    percentage of resources as unused. This is because of the concern of
    load spikes of tenant applications. Later, we will deploy more
    dynamic mechanism in the future version of Ostro.

-   Runtime update via the Oslo message bus or RO Working on this.

-   Migration tip Working on this.
