/*
 * this aggregation pipeline merges clusters sharing the same pangolin_id
 * clusters with etherogeneous pangolin_id are split into separate clusters
 */

pipeline = [{$addFields: {
  /* Take note of the _id of this cluster */
  cluster_id: '$_id'
}}, {$match: {
  /* Consider only clusters having at least one pango id, then (through project,unwind,project,match) pivot the data structure so to have each pangolin_id referencing a cluster_id */
  'aliases.org': 'pango'
}}, {$project: {
  /* the two following projects drop the fields that are useless for creating the new groups (now we need just aliases and cluster_id; we'll get the rest later) */
  cluster_id: 1,
  aliases: 1
}}, {$unwind: {
  path: '$aliases',
  preserveNullAndEmptyArrays: true
}}, {$project: {
  name: '$aliases.name',
  org: '$aliases.org',
  cluster_id: 1,
  _id: 0
}}, {$match: {
  'org': 'pango'
}}, {$group: {
  /* group by pangolin_id and merge their cluster_id */
  _id: '$name',
  cluster_set: {
    $addToSet: '$cluster_id'
  }
}}, {$addFields: {
  /* these addFields, sort and project are just for debugging: they rank the new groups according to the number of merged cluster_id */
  cluster_set_len: {
    $size: "$cluster_set"
  }
}}, {$sort: {
  "cluster_set_len": -1
}}, {$project: {
  "cluster_set_len": false
}}, {$lookup: {
  /* pick the information of each cluster_id */
  from: 'variant',
  localField: 'cluster_set',
  foreignField: '_id',
  as: 'cluster'
}}, {$project: {
  /* drop "cluster_set" (we don't need it anymore) */
  'aliases': "$cluster.aliases",
    'org_2_aa_changes': '$cluster.org_2_aa_changes',
    'org_2_nuc_changes': '$cluster.org_2_nuc_changes',
    'effects': '$cluster.effects'
}}, {$project: {
  /* concatenate arrays of aliases/variant characterizations and effects into single top-level elements */
  'aliases': {
    $reduce: {
      input: '$aliases',
      initialValue: [],
      in: {
        $concatArrays: ['$$value', '$$this']
      }
    },
    /* also eliminate duplicate aliases */
    $reduce: {
      input: '$aliases',
      initialValue: [],
      in: {
        $setUnion: ['$$value', '$$this']
      }
    }
  },
  'org_2_aa_changes': {
    $reduce: {
      input: '$org_2_aa_changes',
      initialValue: [],
      in: {
        $concatArrays: ['$$value', '$$this']
      }
    }
  },
  'org_2_nuc_changes': {
    $reduce: {
      input: '$org_2_nuc_changes',
      initialValue: [],
      in: {
        $concatArrays: ['$$value', '$$this']
      }
    }
  },
  'effects': {
    $reduce: {
      input: '$effects',
      initialValue: [],
      in: {
        $concatArrays: ['$$value', '$$this']
      }
    }
  }
}}, {$project: {
  /* Remove possible pangolin_id different from the new group _id (original clusters can have more than one pangolin_id). The result will be separate identical groups for each pangolin_id that were originally together */
  'aliases': {
    $filter: {
      input: '$aliases',
      as: "x",
      cond: {
        $not: {
          $and: [
            {$eq: ['$$x.org', 'pango']},
            {$not: {
              $eq: ['$$x.name', '$_id']
            }}
          ]
        }
      }
    }
  },
  'org_2_aa_changes': 1,
  'org_2_nuc_changes': 1,
  'effects': 1
}}, {$unionWith: {
  /* Add those clusters that have been excluded at the beginning because not associated to any pangolin_id */
  coll: 'variant',
  pipeline: [
    { $match: {"aliases.org": { $ne: 'pango'}} }
  ]
}}, {$out: {
 /* save */   // TODO rename this reference after test
 coll: 'variant'
}}]
db.variant.aggregate(pipeline)
