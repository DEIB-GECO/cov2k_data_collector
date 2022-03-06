# CoV2K API - Use cases 

## Use case 1

### What are the characteristics (Grantham distance and type) of the residue changes of the Alpha variant

Query: [/combine/aa_residue_changes/aa_positional_changes/contexts/variants?naming_id=Alpha](http://gmql.eu/cov2k/api/combine/aa_residue_changes/aa_positional_changes/contexts/variants?naming_id=Alpha)

Result ...

## Use case 2

### Which amino acid changes of VOC-20DEC-02 fall within the Receptor Binding Domain (RBD)?

Query: [/combine/aa_positional_changes/contexts/variants?naming_id=VOC-20DEC-02](http://gmql.eu/cov2k/api/combine/aa_positional_changes/contexts/variants?naming_id=VOC-20DEC-02)

Result ....

## Use case 3

### Which are the effects of the variants that include the Spike amino acid change D614G?

Query: [/combine/effects/variants/contexts/aa_positional_changes/S:D614G](http://gmql.eu/cov2k/api/combine/effects/variants/contexts/aa_positional_changes/S:D614G)

Result ....

## Use case 4

### Which epitopes are impacted by amino acid changes with documented effects on the binding affinity to the host cell receptors?

Query: [/combine/epitopes/aa_positional_changes/effects?type=binding_to_host_receptor&limit=100&page=1](http://gmql.eu/cov2k/api/combine/epitopes/aa_positional_changes/effects?type=binding_to_host_receptor&limit=100&page=1)

Result ...


