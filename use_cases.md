# CoV2K API - Content exploration

We provide a simple RESTfulAPI (base URL: http://gmql.eu/cov2k/api/) 
that exposes one endpoint for each entity of CoV2K (see schema below),
e.g., for the _Evidence_ entity we use the endpoint [/evidences](http://gmql.eu/cov2k/api/evidences).

<img width="1139" alt="image" src="https://user-images.githubusercontent.com/11488353/157055610-1b7a5292-8356-4dbc-9e4e-2d1b935a6032.png">

For each endpoint, there are four possible uses:

1. Without parameters (e.g., [/evidences](http://gmql.eu/cov2k/api/evidences)), returning all the instances of the entity.
1. With a path parameter specifying the entity identifier (e.g., [/evidences/6215f9756db69cf570802534](https://gmql.eu/cov2k/api/evidences/6215f9756db69cf570802534)), returning only the instance with the given identifier.
1. With a query parameter specifying an attribute-value pair for that entity (e.g., [/evidences?type=preprint](https://gmql.eu/cov2k/api/evidences?type=preprint)), returning the set of evidences with the given type.
1. With a query parameter linking that entity to another entity through a relationship (e.g., [/evidences?effect_id=61a10771969bdc8874782f50](https://gmql.eu/cov2k/api/evidences?effect_id=61a10771969bdc8874782f50)), returning the set of instances of the first entity that are linked to the instances of the second entity with the specified identifier.

Note that, given two entities X and Y connected by a relationship, it is possible to extract the instances of one of them connected to a given instance of the other one.
Recall that entity names are unique and that entity identifiers are constructed from entity names (i.e., `<entity_name>_id`).
Users can control the production of results of queries by means of 
pagination parameters `limit` and `page`;
the former sets the number of instances to be produced within a page of results
(e.g., 100), the latter indicates the specific page to be displayed. 
Pagination is mandatory for the queries over data entities (e.g., _Sequence_, _AA change_...) as they may return very large results.

Note that the endpoint [/effects](http://gmql.eu/cov2k/api/effects) accepts as path parameters identifiers of variants, of groups of amino acid changes, or of single amino acid changes.
Moreover, given that each residue change is connected to exactly two residues,
the endpoint [/aa_residues](http://gmql.eu/cov2k/api/aa_residues)
invoked on a given `aa_residue_change_id` returns two instances corresponding to the reference and alternative residues, whereas two specific endpoints [/aa_residues_ref](http://gmql.eu/cov2k/api/aa_residues_ref) (resp. [/aa_residues_alt](http://gmql.eu/cov2k/api/aa_residues_alt)) can be used to return only information regarding the reference (resp. alternative) residue.
 
The relationships of the abstract model can be combined (chained) one after the other through the [/combine](http://gmql.eu/cov2k/api/combine) endpoint, which cannot be used alone but needs other path parameters.
For example [http://gmql.eu/cov2k/api/combine/evidences/effects?aa_positional_change_id=S:L452R](http://gmql.eu/cov2k/api/combine/evidences/effects?aa_positional_change_id=S:L452R) extracts the evidences reporting effects on the Spike mutation L452R.
Pagination applies to the combination result and is mandatory if the combination result refers to a data entity.

A basic error handling mechanism prohibits users to build combinations with cycles (i.e., strings with repeated entities are illegal).
Using path parameters that are not part of the last specified entity is also not allowed (e.g., [/epitopes/variant_id=B.1.1.7](http://gmql.eu/cov2k/api/epitopes/variant_id=B.1.1.7) is illegal). 

Finally,
as intermediate results of combinations may be quite large, we set a maximum threshold on their size (say 10,000
instances); when the threshold is overcome, the query fails and the user can then use shorter combinations or more restrictive query conditions.

# CoV2K API - Use cases 

## Use case 1

### What are the characteristics (Grantham distance and type) of the residue changes of the Alpha variant?

Some of the instances  involved in this query are represented in the figure below.

<img width="1321" alt="image" src="https://user-images.githubusercontent.com/11488353/157043547-66e56a74-e127-478e-bf23-d950695f9160.png">

Let V1 be the identifier of the variant having Alpha as name (provided by the WHO organization). 
For evaluating its characteristic amino acid changes, we need to consider all the positional changes included in the contexts defined for V1 (in the current implementation, we include the ones defined by the owners CoVariants and Public Health England). 
Then, for all such positional changes, we consider the involved residue changes and extract their information, including the Grantham distance and type (radical or conservative).

On CoV2K API we can perform the following query:

[/combine/aa_residue_changes/aa_positional_changes/contexts/variants?naming_id=Alpha](http://gmql.eu/cov2k/api/combine/aa_residue_changes/aa_positional_changes/contexts/variants?naming_id=Alpha)

The result contains 15 _AA residue changes_; the first three elements of the result are the following.
<img width="1031" alt="image" src="https://user-images.githubusercontent.com/11488353/157050212-7a2da042-5685-4f19-bc59-a458ebaf8534.png">
They represent three radical changes with respectively 126, 94, and 81 values for [Grantham distance](http://www.jstor.org/stable/1739007). The first one, as an example, represents a change from D (Aspartic Acid) to A (Alanine).

## Use case 2

### Which amino acid changes of VOC-20DEC-02 fall within the Receptor Binding Domain (RBD)?

We extract the amino acid positional changes related to the requested Variant of Concern, with the following query:

[/combine/aa_positional_changes/contexts/variants?naming_id=VOC-20DEC-02](http://gmql.eu/cov2k/api/combine/aa_positional_changes/contexts/variants?naming_id=VOC-20DEC-02)

The result has 21 elements. From now on, the API can be used to understand which elements fall within the Receptor-binding domain.

*Step 1:*
A list of regions within the Spike protein can be extracted as follows:

[/protein_regions?protein_id=S](http://gmql.eu/cov2k/api/protein_regions?protein_id=S)

Manual inspection of the list leads to identify an element with `name` "receptor-binding domain (rbd)"
that falls within the 319 and 541 positions of the Spike protein. 
Of course, if the user had known from the beginning how the RBD is encoded as a string in UniProtKB, she chould have directly called:

[/protein_regions?name=receptor-binding domain (rbd)](http://gmql.eu/cov2k/api/protein_regions?name=receptor-binding%20domain%20(rbd))

<img width="1059" alt="image" src="https://user-images.githubusercontent.com/11488353/157054173-b357144a-43cb-4247-a60b-1405f1e0dc78.png">

*Step 2:*
We then inspect the list of changes characterizing variant VOC-20DEC-02, 
looking for those whose:

1. `protein_id` is protein S;
1. `position` is included within the `start_on_protein` (319) and `stop_on_protein` (540) range of RBD.

Only four _AA positional changes_ out of the initial 21 in the result occur within the chosen coordinates.

<img width="1085" alt="image" src="https://user-images.githubusercontent.com/11488353/157054650-951ad706-d377-45bb-9c5f-bb64b8c718a6.png">
<img width="1084" alt="image" src="https://user-images.githubusercontent.com/11488353/157054754-541ccc92-d640-4eb4-8398-c23928264c90.png">
<img width="1088" alt="image" src="https://user-images.githubusercontent.com/11488353/157054810-c3b6eba9-9ba6-48e2-82b9-b0e1cde882b5.png">
<img width="1083" alt="image" src="https://user-images.githubusercontent.com/11488353/157054888-b45d3222-e101-479c-9bdd-8a76d2235f31.png">


## Use case 3

### Which are the effects of the variants that include the Spike amino acid change D614G?

We interpret this query as the effects of variants that include D614G in at least one of their contexts.
We first extract the S:D614G change, then we get all contexts that contain it;
from the context we understand the related variants and, finally, we reach the effects of each of them.

The following query achieves the intended result:

[/combine/effects/variants/contexts/aa_positional_changes/S:D614G](http://gmql.eu/cov2k/api/combine/effects/variants/contexts/aa_positional_changes/S:D614G)

A total of 115 effect records are extracted; the first three elements of the result are the following.
<img width="1029" alt="image" src="https://user-images.githubusercontent.com/11488353/157050325-593c45f9-83b3-449a-acef-6a6b96d5987f.png">

The publications linked to each of the effects can be checked using the [/evidences](https://gmql.eu/cov2k/api/evidences) endpoint with a specific `epitope_id`, for example:

https://gmql.eu/cov2k/api/evidences?effect_id=61a10781969bdc8874783f87


## Use case 4

### Which epitopes are impacted by amino acid changes with documented effects on the binding affinity to the host cell receptors?

First, we can use the [/effects/](http://gmql.eu/cov2k/api/effects) endpoint to check possible values for the `type` attribute. 
A complete list of values and their definitions is available [here](https://github.com/DEIB-GECO/cov2k_data_collector/blob/master/CoV2K_Effects_Taxonomy.pdf).

As a first operation, effects of `type` "binding_to_host_receptor" are extracted; 
then amino acid positional changes connected to such effects are retrieved and their `positions` are intersected with the range [`epitope_start`,`epitope_stop`]. Only epitopes that include at least one of the considered changes are returned in the result.
As an example, we can perform the request:

[/combine/epitopes/aa_positional_changes/effects?type=binding_to_host_receptor&limit=100&page=1](http://gmql.eu/cov2k/api/combine/epitopes/aa_positional_changes/effects?type=binding_to_host_receptor&limit=100&page=1)

As the combination includes a data entity (epitope), pagination parameters must be provided; 
follow-up queries which consider the next pages (e.g., 2,3,...) can be used to further inspect the results.
Up to a given limit one can load subsequent pages.

We here show the first three elements of the first page with 100 elements:

<img width="1091" alt="image" src="https://user-images.githubusercontent.com/11488353/157051737-6a102393-dce9-4cf1-af01-2183279c3e31.png">
