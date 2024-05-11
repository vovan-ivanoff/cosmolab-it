$(document).ready(function () {
    var socket = io.connect("http://localhost:5000/single");
    var d;
    var t;
    $("#quiz").hide();
    $("#startBtn").on("click", function () {
      $("#results").hide();
      theme = $('input[name="themes"]:checked').val();
      socket.emit("start", theme);
    });
    socket.on("pcount", function (data) {
      $("#pcount").text(data);
    });
    socket.on("themes", function (data) {
      console.log(data);
      for (let i = 0; i < data.length; i++) {
        tmpl = `<input type="radio" name="themes" value="${data[i]}">${data[i]}}</input><br>`;
        $("#results").append(tmpl);
      }
    });
    socket.on("question", function (data) {
      $("#quiz").show();
      $("#results").hide();
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
          socket.emit("s_answer", "not-corr");
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
    $("#ansBtn").on("click", function () {
      if ($('input[name="answers"]:checked').val() == d["correct"]) {
        socket.emit("answer", "corr");
      } else {
        socket.emit("answer", "not_corr");
      }
      t.stop();
    });
    socket.on("end", function (data) {
      res = "";
      for (var i in data) {
        res += i + " - "; // alerts key
        res += data[i] + "<br>"; //alerts key's value
      }
      $("#quiz").hide();
      $("#results").html(res);
      $("#results").show();
    });
  });
  