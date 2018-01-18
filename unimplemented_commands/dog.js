// Description
//   Like !cat, but for dog people (and with less trauma for 2310 students).
//
// Commands:
//   `!dog` - Like !cat, but for dog people.

module.exports = function (robot) {
	robot.respond(/!?dog/i, function (res) {
		res.send("```\n" +
            "                                __\n" +
            "         ,                    ,\" .\`--o\n" +
            "        ((                   (  | __,\'\n" +
            "         \\\\~----------------' \\_;/\n" +
            "         (                      /\n" +
            "         /) ._______________.  )\n" +
            "        (( (               (( (         hjw\n" +
            "         \`\`-\'               \`\`-\'\n\n```");
  });
};
