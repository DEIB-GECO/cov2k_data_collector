pipeline = [
    {
        $project: {
            protein_name: 1
        }
    }, {
        $group: {
            _id: "$protein_name"
        }
    }, {
        $lookup: {
            from: 'structure',
            localField: '_id',
            foreignField: 'protein_characterization.protein_name',
            as: 'joined'
        }
    }, {
        $match: {
            "joined.0": {$exists: true}
        }
    }, {
        $project: {
            _id: 1
        }
    }, {
        $lookup: {
            from: 'protein_region',
            localField: '_id',
            foreignField: 'protein_name',
            as: 'protein_regions_of_described_proteins'
        }
    }, {
        $project: {
            protein_regions_of_described_proteins: 1, _id: 0
        }
    }, {
        $unwind: {
            path: "$protein_regions_of_described_proteins"
        }
    }, {
        $replaceWith: {
            _id: "$protein_regions_of_described_proteins._id",
            protein_name: "$protein_regions_of_described_proteins.protein_name",
            start_on_prot: "$protein_regions_of_described_proteins.start_on_prot",
            stop_on_prot: "$protein_regions_of_described_proteins.stop_on_prot",
            description: "$protein_regions_of_described_proteins.description",
            type: "$protein_regions_of_described_proteins.type"
        }
    }, {$out: 'protein_region'}]
db.protein_region.aggregate(pipeline)