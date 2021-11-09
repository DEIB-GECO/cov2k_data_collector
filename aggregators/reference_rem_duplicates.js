pipeline = [
    {$unwind: "$effect_ids"},
    { $group: {
        _id: {
            uri: '$uri',
            citation: '$citation',
            type: '$type',
            publisher: '$publisher'
        },
        effect_ids: {$addToSet: "$effect_ids"},
    } },
    {$project: {
        _id: false,
        effect_ids: true,
        citation: "$_id.citation",
        type: "$_id.type",
        uri: "$_id.uri",
        publisher: "$_id.publisher"
    } },
    {$out: "aggr_reference"}    // TODO rename this reference after test
]
db.reference.aggregate(pipeline)