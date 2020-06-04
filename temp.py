htmlContent = """
<!DOCTYPE html>
<html>
    <head>
        <meta charset="utf-8"/>
        <title>Transperth Journey Planner</title>
        <script src="https://ajax.googleapis.com/ajax/libs/jquery/3.5.1/jquery.min.js"></script>
        <link rel="stylesheet" href="https://stackpath.bootstrapcdn.com/bootstrap/4.4.1/css/bootstrap.min.css" integrity="sha384-Vkoo8x4CGsO3+Hhxv8T/Q5PaXtkKtu6ug5TOeNV6gBiFeWPGFN9MuhOf23Q9Ifjh" crossorigin="anonymous">
    </head>
    <body>
        <div class="container">
            {summarisedTrip}
            <br>
            <div class="card">
                <div class="card-header">
                    Plan your next trip
                </div>
                <div class="card-body">
                    <form action="{stationTcpAddress}" method="GET" >
                        <div>
                            <label for="source">Source:</label>
                            <b><p name="source" id="source">{station}</p></b>
                        </div>
                        <div>
                            <label for="to">Destination:</label>
                            <input name="to" id="to" class="form-control">
                        </div>
                        <div>
                            <label for="time">Departure Time:</label>
                            <select name="time" id="timetable" class="form-control"></select>
                        </div>
                        <div>
                            <label for="tripType">Type of Trip:</label>
                            <select name="tripType" id="tripType" class="form-control"></select>
                        </div>
                        <br>
                        <div>
                            <input type="submit" value="Get trip details" class="btn btn-primary">
                        </div>
                    </form>
                </div>
            </div>
            
            <div id="response">
                <br>
                <hr>
                <h4>Trip Details</h4>
                <br>
                <div class="card">
                    <ul id="response-list" class="list-group list-group-flush">
                    </ul>
                </div>
            </div>
        </div>
    </body>
</html>

<script type="text/javascript">

    const timetable = {timetable};
    const tripTypes = {tripTypes};
    const stationResponse = {stationResponse};
    const responses = {responses};
    const routeEndFound = {routeEndFound};

    const respond = (response, $response, $responseList, routeEndFound) => {
        $response.show();
        if(routeEndFound){
            $responseList.append(
                `<li class="list-group-item">Oh uh! No route found!</li>`
            );
        } else {
            responses.forEach( (response, index) => {
                list = `<li class="list-group-item">
                            <span class="badge badge-secondary badge-pill"> ${index+1}</span>
                            Depart from <b>${response[0]}</b> (<b>${response[3]}</b>) at <b>${response[1]}</b> taking <b>${response[2]}</b> and arrive at
                            <b>${response[5]}</b> at <b>${response[4]}</b>.
                        </li>`
                $responseList.append(list);
            });
        }
    }

    const updateTimetable = ($timetable) => {
        timetable.map(record => $('<option>')
            .attr({ value : record[0] })
            .text(record[0])
        ).forEach($option => $timetable.append($option));
    }

    const updateTripType = ($tripType) => {
        tripTypes.map(record => $('<option>')
            .attr({ value : record })
            .text(record)
        ).forEach($option => $tripType.append($option));
    }

    $(() => {
        const $timetable = $("#timetable");
        const $tripType = $("#tripType");
        const $response = $("#response")
        const $responseList = $("#response-list")
        $response.hide();
        updateTimetable($timetable);
        updateTripType($tripType);
        if(stationResponse){
            respond(responses, $response, $responseList, routeEndFound);
        }
    });
</script>
"""
