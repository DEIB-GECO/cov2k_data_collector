pipeline_on_effect = [
    {
        // group effects on all attributes (type,lv,method,aa_changes)
        // and collect their _id into an array
        $group: {
            _id: {
                type: "$type",
                lv: "$lv",
                method: "$method",
                aa_changes: "$aa_changes"
            },
            collected_effect_ids: {$addToSet: "$_id"}
        }
    },
    // The following are for inspecting the pipeline at this point:
    // It sorts the groups by size of  collected_effect_ids in descending order.
    //     {
    //     $addFields: {
    //         array_len: {$size: "$collected_effect_ids"}
    //     }
    // }, {
    //     $sort: {
    //         array_len: -1
    //     }
    // },
        {
        // ad a temporary variable that helps slicing the array of collected IDs
        $addFields: {
            slice_from_idx: {$subtract: [0, {$subtract: [{$size: "$collected_effect_ids"}, 1]}]}
        }
    }, {
        // make first item of the array the ID of the effect.
        // leave the others into effects_to_eliminate
        $project: {
            _id: {$first: "$collected_effect_ids"},
            type: "$_id.type",
            lv: "$_id.lv",
            method: "$_id.method",
            aa_changes: "$_id.aa_changes",
            effects_to_eliminate: {
                $slice: ["$collected_effect_ids", "$slice_from_idx"]
            }
        }
    }, {$out: 'effect'}     // Replace effects!


    // Stuff no more useful
    // {
    //     $project: {
    //         _id: 1,
    //         effects_to_eliminate: 1
    //     }
    // }, {
    //     $unwind: {
    //         path: "$effects_to_eliminate",
    //         preserveNullAndEmptyArrays: false
    //     }
    // }, {
    //     $lookup: {
    //         from: 'evidence',
    //         let: {effect_to_elim: "$effects_to_eliminate"},
    //         pipeline: [
    //             {
    //                 $match: {
    //                     $expr: {
    //                         $in: ["$$effect_to_elim", "$effect_ids"]
    //                     }
    //                 }
    //             }
    //         ],
    //         as: 'joined'
    //     }
    // }, {
    //     $unwind: {
    //         path: "$joined",
    //         preserveNullAndEmptyArrays: false
    //     }
    // }, {
    //     $project: {
    //         _id: "$joined._id",
    //         effect_to_add: "$_id",
    //         effect_ids: {
    //             $filter: {
    //                 input: "$joined.effect_ids",
    //                 as: "an_effect_id",
    //                 cond: {$ne: ["$$an_effect_id", "$effects_to_eliminate"]}
    //             }
    //
    //         },
    //         citation: "$joined.citation",
    //         type: "$joined.type",
    //         uri: "$joined.uri",
    //         publisher: "$joined.publisher"
    //     }
    // }
    ]
db.effect.aggregate(pipeline_on_effect)

pipeline_on_evidence = [
    {
        // split evidences on each linked effect_id
        $unwind: {
            path: "$effect_ids",
            preserveNullAndEmptyArrays: false
        }
    },
    // Used only to insepct the final result by selecting only specific evidences
    //     {
    //     // prendi una evidence con un effetto da eliminare
    //     _id: ObjectId('61969b8c6755515fd8b6c242')
    //     // o una evidenza senza effetti da eliminare
    //     //_id: ObjectId('61708df5de205ac13103d9d0')
    // },
        {
        // join each doc (an evidence) with its effect, but only if it is an effect to be eliminated
        // else "effect_if_to_eliminate" remains empty
        $lookup: {
            from: 'effect',
            let: {one_effect_of_this_evidence: "$effect_ids"},
            pipeline: [
                {
                    $match: {
                        $expr: {
                            $in: ["$$one_effect_of_this_evidence", "$effects_to_eliminate"]
                        }
                    }
                }
            ],
            as: 'effect_if_to_eliminate'
        }
    }, {
        // unnest the joined effects (cardinality can be only 0 or 1 by construction)
        $unwind: {
            path: "$effect_if_to_eliminate",
            preserveNullAndEmptyArrays: true
        }
    }, {
        // if the join produced a non-empty collection of effect_if_to_eliminate,
        // (meaning that this doc references an effect to eliminate)
        // replace the effect of this doc (an evidence) with the _id of the
        // joined effect (the correct _id of the effect)
        // ELSE
        // (if the doc references an effect that is not in the "effect_to_eliminate")
        // keep the effect_id that was referenced originally by this doc (evidence)
        $project: {
            _id: "$_id",
            citation: "$citation",
            type: "$type",
            uri: "$uri",
            publisher: "$publisher",
            a_correct_effect_of_this_evidence: {
                $ifNull: ["$effect_if_to_eliminate._id", "$effect_ids"]
            }
        }
    },
        // We updated the effect_ids and removed the references to the effects to eliminate
        // We must reconstruct the original effects by grouping them based on the _id and
        // collect the referenced effect_ids into an array. See the commented code
    //     {
    //     $group: {
    //         _id: {
    //             _id: "$_id",
    //             citation: "$citation",
    //             type: "$type",
    //             uri: "$uri",
    //             publisher: "$publisher",
    //         },
    //         effect_ids: {$addToSet: "$a_correct_effect_of_this_evidence"}
    //     }
    // }, {
    //     $project: {
    //         _id: "$_id._id",
    //         citation: "$_id.citation",
    //         type: "$_id.type",
    //         uri: "$_id.uri",
    //         publisher: "$_id.publisher",
    //         effect_ids: 1
    //     }
    // },
        // But we can advance another problem: evidences could have been inserted twice
        // by the ETL pipeline. To fix also this, in the $group, we group on all the
        // attributes of an evidence, except for the _id -> Same evidences are grouped
        // together and effects are summed up.


        {
        $group: {
            _id: {
                citation: "$citation",
                type: "$type",
                uri: "$uri",
                publisher: "$publisher",
              },
            effect_ids: {$addToSet: "$a_correct_effect_of_this_evidence"}
        }
    }, {
        $project: {
              citation: "$_id.citation",
              type: "$_id.type",
              uri: "$_id.uri",
              publisher: "$_id.publisher",
              effect_ids: "$effect_ids",
              _id: false
        }
    }, {$out: 'evidence'}     // Replace evidence!
    ]
db.evidence.aggregate(pipeline_on_evidence)


pipeline_on_variant = [
    {
        $unwind: {
            path: "$effects",
            preserveNullAndEmptyArrays: true
        }
    }, {
        $sort: {
            effects: -1
        }
    }, {
        $lookup: {
            from: 'effect',
            let: {one_effect_of_this_variant: "$effects"},
            pipeline: [
                {
                    $match: {
                        $expr: {
                            $in: ["$$one_effect_of_this_variant", "$effects_to_eliminate"]
                        }
                    }
                }
            ],
            as: 'effect_if_to_eliminate'
        }
    }, {
        $unwind: {
            path: "$effect_if_to_eliminate",
            preserveNullAndEmptyArrays: true
        }
    }, {
        $project: {
            _id: "$_id",
            aliases: "$aliases",
            org_2_aa_changes: "$org_2_aa_changes",
            org_2_nuc_changes: "$org_2_nuc_changes",
            effects: {
                $ifNull: ["$effect_if_to_eliminate._id", "$effects"]
            }
        }
    }, {
        $group: {
            _id: "$_id",
            aliases: {$addToSet: "$aliases"},
            org_2_aa_changes: {$addToSet: "$org_2_aa_changes"},
            org_2_nuc_changes: {$addToSet: "$org_2_nuc_changes"},
            effects: {$addToSet: "$effects"}
        }
    }, {$out: "variant"}]
db.variant.aggregate(pipeline_on_variant)


// remove effects_to_eliminate_from_collection
pipeline_on_effect_last_step = [
    {$unset: "effects_to_eliminate"
    }, {$out: 'effect'}
]
db.effect.aggregate(pipeline_on_effect_last_step)