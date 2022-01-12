// THIS IS THE SAME FILE as the one in this folder with the same name, but without comments

pipeline_on_effect = [{$group: {
  _id: {
    type: "$type",
    lv: "$lv",
    method: "$method",
    aa_changes: "$aa_changes"
  },
  collected_effect_ids: {
    $addToSet: "$_id"
  }
}}, {$addFields: {
  slice_from_idx: {
    $subtract: [0, {
      $subtract: [{
        $size: "$collected_effect_ids"
      }, 1]
    }]
  }
}}, {$project: {
  _id: {
    $first: "$collected_effect_ids"
  },
  type: "$_id.type",
  lv: "$_id.lv",
  method: "$_id.method",
  aa_changes: "$_id.aa_changes",
  effects_to_eliminate: {
    $slice: ["$collected_effect_ids", "$slice_from_idx"]
  }
}}, {$out: 'effect'}]
db.effect.aggregate(pipeline_on_effect)


pipeline_on_evidence = [
    {
        $unwind: {
            path: "$effect_ids",
            preserveNullAndEmptyArrays: false
        }
    }, {
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
        $unwind: {
            path: "$effect_if_to_eliminate",
            preserveNullAndEmptyArrays: true
        }
    }, {
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
    }, {
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
    }, {$out: 'evidence'}
]
db.evidence.aggregate(pipeline_on_evidence)


// pipeline_on_variant = [
//     {
//         $unwind: {
//             path: "$effects",
//             preserveNullAndEmptyArrays: true
//         }
//     }, {
//         $sort: {
//             effects: -1
//         }
//     }, {
//         $lookup: {
//             from: 'effect',
//             let: {one_effect_of_this_variant: "$effects"},
//             pipeline: [
//                 {
//                     $match: {
//                         $expr: {
//                             $in: ["$$one_effect_of_this_variant", "$effects_to_eliminate"]
//                         }
//                     }
//                 }
//             ],
//             as: 'effect_if_to_eliminate'
//         }
//     }, {
//         $unwind: {
//             path: "$effect_if_to_eliminate",
//             preserveNullAndEmptyArrays: true
//         }
//     }, {
//         $project: {
//             _id: "$_id",
//             aliases: "$aliases",
//             org_2_aa_changes: "$org_2_aa_changes",
//             org_2_nuc_changes: "$org_2_nuc_changes",
//             effects: {
//                 $ifNull: ["$effect_if_to_eliminate._id", "$effects"]
//             }
//         }
//     }, {
//         $group: {
//             _id: "$_id",
//             aliases: {$addToSet: "$aliases"},
//             org_2_aa_changes: {$addToSet: "$org_2_aa_changes"},
//             org_2_nuc_changes: {$addToSet: "$org_2_nuc_changes"},
//             effects: {$addToSet: "$effects"}
//         }
//     }, {$out: "variant"}]
//                                THE ABOVE PIPELINE HAS A BUG. THE NEW ONE FIXES IT BUT MUST BE TESTED
pipeline_on_variant = [{$unwind: {
  path: "$effects",
  preserveNullAndEmptyArrays: true
}}, {$sort: {
  effects: -1
}}, {$lookup: {
  from: 'effect',
  let: {
    one_effect_of_this_variant: "$effects"
  },
  pipeline: [{
    $match: {
      $expr: {
        $in: ["$$one_effect_of_this_variant", "$effects_to_eliminate"]
      }
    }
  }],
  as: 'effect_if_to_eliminate'
}}, {$unwind: {
  path: "$effect_if_to_eliminate",
  preserveNullAndEmptyArrays: true
}}, {$project: {
  _id: "$_id",
  aliases: "$aliases",
  org_2_aa_changes: "$org_2_aa_changes",
  org_2_nuc_changes: "$org_2_nuc_changes",
  effects: {
    $ifNull: ["$effect_if_to_eliminate._id", "$effects"]
  }
}}, {$group: {
  _id: "$_id",
  effects: {
    $addToSet: "$effects"
  }
}}, {$lookup: {
  from: ' variant',
  localField: '_id',
  foreignField: ':_id',
  as: 'v_attr'
}}, {$unwind: {
  path: "$v_attr",
  preserveNullAndEmptyArrays: true
}}, {$project: {
  _id: 1,
  aliases: "$v_attr.aliases",
  org_2_aa_changes: "$v_attr.org_2_aa_changes",
  org_2_nuc_changes: "$v_attr.org_2_nuc_changes",
  effects: 1
}}, {$out: "variant"}]
db.variant.aggregate(pipeline_on_variant)


/*remove effects_to_eliminate_from_collection*/
pipeline_on_effect_last_step = [
    {$unset: "effects_to_eliminate"
    }, {$out: 'effect'}
]
db.effect.aggregate(pipeline_on_effect_last_step)