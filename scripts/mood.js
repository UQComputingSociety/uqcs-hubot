// Description
//   Keeps track of user moods
//
// Commands:
//   !`mood` <username> - Outputs the mood of the user
//   !`happiest` - Outputs the happiest person
//   !`saddest` - Outputs the saddest person
//
module.exports = function (robot) {
	robot.hear(/(:<|:\(|:'\()/, function (res) {
		var moods = robot.brain.get("moods");
		if(moods === null) {
			robot.brain.set("moods", {});
			moods = robot.brain.get("moods");
			if(moods === null) { return; }
		}
		var name = res.message.user.name.toLowerCase();
		if(moods[name] === undefined) {
			moods[name] = -1;
		}else {
			moods[name]--;
		}
	});

	robot.hear(/(:>|:\)|:'\))/, function (res) {
		var moods = robot.brain.get("moods");
		if(moods === null) {
			robot.brain.set("moods", {});
			moods = robot.brain.get("moods");
			if(moods === null) { return; }
		}
		var name = res.message.user.name.toLowerCase();
		if(moods[name] === undefined) {
			moods[name] = 1;
		}else {
			moods[name]++;
		}
	});

	robot.respond(/!?mood (.+)/i, function(res) {
		var moods = robot.brain.get("moods");
		if(moods === null) {
			res.send("Brain not loaded.\r\n");
			return;
		}

		var target = res.match[1].toLowerCase();
		if(moods[target] === undefined) {
			res.send(target + " is emotionless...\r\n");
		}else {
			if(moods[target] == 0) {
				res.send(target + " is neutral.\r\n");
			}else if(moods[target] > 0) {
				res.send(target + " is happy!\r\n");
			}else {
				res.send(target + " is sad... Try cheer them up!\r\n");
			}
		}
	});

	robot.respond(/!?(happiest|saddest)/i, function(res) {
		var moods = robot.brain.get("moods");
		if(moods === null) {
			res.send("Brain not loaded.\r\n");
			return;
		}

		var max;
		var min;
		var m = moods;
		for(var p in m) {
			if(max === undefined || m[p] > m[max]) { max = p; }
			if(min === undefined || m[p] < m[min]) { min = p; }
		}

		if(res.match[1] === "happiest") {
			res.send(max + " was the happest! YAY " + max + "!!!\r\n");
		}else {
			res.send(min + " was the saddest... Poor " + min + "... Everybody try cheer them up!\r\n");
		}
	});

	return new HubotCron("0 0 * * *", "Australia/Brisbane", function() {
		robot.brain.set("moods", {});
	}
};