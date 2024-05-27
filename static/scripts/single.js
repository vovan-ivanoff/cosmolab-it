$(document).ready(function () {
    var socket = io.connect("http://localhost:5000/single");
    var d;
    var t;
    $("#quiz").hide();
    $("#vopros").hide();
    $("#startBtn").on("click", function () {
      $("#results").hide();
      theme = $('input[name="themes"]:checked').val();
      socket.emit("start", theme);
    });
    $("#ans0").on("click", function () {
      if (d["correct"] == 0) {
        socket.emit("answer", "corr");
      }
      else {
        socket.emit("answer", "not_corr");
      }
      t.stop();
    });
    $("#ans1").on("click", function () {
      if (d["correct"] == 1) {
        socket.emit("answer", "corr");
      } else {
        socket.emit("answer", "not_corr");
      }
      t.stop();
    });
    $("#ans2").on("click", function () {
      if (d["correct"] == 2) {
        socket.emit("answer", "corr");
      } else {
        socket.emit("answer", "not_corr");
      }
      t.stop();
    });
    $("#ans3").on("click", function () {
      if (d["correct"] == 3) {
        socket.emit("answer", "corr");
      } else {
        socket.emit("answer", "not_corr");
      }
      t.stop();
    });
    socket.on("themes", function (data) {
      console.log(data);
      for (let i = 0; i < data.length; i++) {
        tmpl = `<input type="radio" name="themes" class="variation" value="${data[i]}">${data[i]}</input><br>`;
        $("#results").append(tmpl);
      }
    });
    socket.on("question", function (data) {
      $("#quiz").show();
      $("#results").hide();
      $("#vopros").show();
      $("#vopros").text(data["question"]);
      d = data;
      for (let i = 0; i < 4; i++) {
        console.log("#ans" + i.toString());
        console.log(data["answers"][i]);
        $("#ans" + i.toString()).text(data["answers"][i]);
      }
      t = new Stopwatch({
        element: $("#countdown"), // DOM element
        paused: false, // Status
        elapsed: data["time"] * 1000, // Current time in milliseconds
        countingUp: false, // Counting up or down
        timeLimit: 0, // Time limit in milliseconds
        updateRate: 1000, // Update rate, in milliseconds
        onTimeUp: function () {
          // onTimeUp callback
          this.stop();
          socket.emit("answer", "not-corr");
        },
        onTimeUpdate: function () {
          // onTimeUpdate callback
          var t = this.elapsed,
            m = ("0" + Math.floor((t % 3600000) / 60000)).slice(-2),
            s = ("0" + Math.floor((t % 60000) / 1000)).slice(-2);
          var formattedTime = m + ":" + s;
          $(this.element).html(formattedTime);
        },
      });
    });
    socket.on("end", function (data) {
      res = "";
      for (var i in data) {
        res += i + " - "; // alerts key
        res += data[i] + "<br>"; //alerts key's value
      }
      $("#quiz").hide();
      $("#vopros").hide();
      $("#results").html(res);
      $("#results").show();
    });
  });
  