pipeline = [{$group: {
  _id: "$change_id"
}}, {$lookup: {
  from: 'aa_change',
  localField: '_id',
  foreignField: 'change_id',
  as: 'group'
}}, {$project: {
  group: {$first: "$group"}
}}, {$replaceWith: {
  _id: "$group._id",
  change_id: "$group.change_id",
  protein: "$group.protein",
  ref: "$group.ref",
  pos: "$group.pos",
  alt: "$group.alt",
  type: "$group.type",
  length: "$group.length",
  is_optional: "$group.is_optional"
}}, {$out: 'aa_change'}]
db.aa_change.aggregate(pipeline)