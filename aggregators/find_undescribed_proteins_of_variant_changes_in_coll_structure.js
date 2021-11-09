pipeline = [{$project: {
  aa_changes: "$org_2_aa_changes.changes"
}}, {$unwind: {
  path: "$aa_changes",
  preserveNullAndEmptyArrays: false
}}, {$unwind: {
  path: "$aa_changes",
  preserveNullAndEmptyArrays: false
}}, {$project: {
  prot: {$first:{$split: ["$aa_changes", ":"]} }
}}, {$group: {
  _id: "$prot"
}}, {$lookup: {
  from: 'structure',
  localField: '_id',
  foreignField: 'protein_characterization.protein_name',
  as: 'join'
}}, {$match: {
  "join": []
}}, {$out: 'proteins_in_variants_missing_characterization'}]
db.variant.aggregate(pipeline)


// result
// "ORF7A"
// "ORF8"
// "ORF3A"
// "ORF9B"
// "ORF6"