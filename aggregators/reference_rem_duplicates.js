pipeline = [{$unwind: "$effect_ids"}, {
    $group: {
        _id: {
            uri: '$uri',
            citation: '$citation',
            type: '$type',
            publisher: '$publisher'
        },
        effect_ids: {
            $addToSet: "$effect_ids"
        }
    }
}, {
    $replaceWith: {
        effect_ids: "$effect_ids",
        citation: "$_id.citation",
        type: "$_id.type",
        uri: "$_id.uri",
        publisher: "$_id.publisher"
    }
}, {$out: "evidence"}]
db.reference.aggregate(pipeline)