import json
import streamlit as st
import pydeck as pdk  # Import pydeck for map visualization
import altair as alt
import pandas as pd
import requests

st.title("🏠 Property Data Dashboard")

# Address and Postcode Input
col1, col2 = st.columns(2)
with col1:
    address = st.text_input("Address")
with col2:
    postcode = st.text_input("Postcode")

if st.button("Submit"):
    try:
        # Read local JSON file instead of API call
        # with open('results.json', 'r', encoding='utf-8') as file:
            # data = json.load(file)
        # Make API request
        url = "https://api.data.street.co.uk/street-data-api/v2/properties/addresses?tier=premium"
        payload = {
            "data": {
                "address": address,
                "postcode": postcode
            }
        }
        headers = {
            'Content-Type': 'application/json',
            'X-Api-Key': st.secrets["DATA_STREET_KEY"]
        }
        
        response = requests.post(url, json=payload, headers=headers)
        data = response.json()

        # Property Details Section
        st.header("Property Overview")
        col1, col2 = st.columns(2)
        with col1:
            try:
                st.subheader("Current Property")
                st.markdown(f"**Address:** {data['data']['attributes']['address']['street_group_format']['address_lines']}")
                st.markdown(f"**Property Type:** {data['data']['attributes']['property_type']['value']}")
                st.markdown(f"**Year Built:** {data['data']['attributes']['year_built']['value']}")
                st.markdown(f"**Council Tax:** {data['data']['attributes']['council_tax']['band']} - £{data['data']['attributes']['council_tax']['current_annual_charge']}")
                st.markdown(f"**Deeds:** {data['data']['attributes']['title_deeds']['titles'][0]['class_of_title']}")
            except:
                st.markdown("Property details unavailable.")

        with col2:
            try:
                st.subheader("Property Details")
                st.markdown(f"**Plot Area:** {data['data']['attributes']['plot']['total_plot_area_square_metres']} sqm")
                st.markdown(f"**Outdoor Space:** {data['data']['attributes']['outdoor_space']['outdoor_space_area_square_metres']} sqm")
                st.markdown(f"**Number of Bedrooms:** {data['data']['attributes']['number_of_bedrooms']['value']}")
                st.markdown(f"**Number of Bathrooms:** {data['data']['attributes']['number_of_bathrooms']['value']}")
            except:
                st.markdown("Detailed property measurements unavailable.")

        # Transactions Section
        st.header("Property Transactions")
        try:
            if data['data']['attributes'].get('transactions') and data['data']['attributes']['transactions']:
                st.subheader("Latest Transaction")
                col1, col2 = st.columns(2)
                with col1:
                    st.markdown(f"**Date:** {data['data']['attributes']['transactions'][0]['date']}")
                    st.markdown(f"**Price:** £{data['data']['attributes']['transactions'][0]['price']}")
                with col2:
                    st.markdown(f"**Property Type:** {data['data']['attributes']['transactions'][0]['property_type']}")
                    st.markdown(f"**Transaction ID:** {data['data']['attributes']['transactions'][0]['transaction_id']}")
            else:
                st.markdown("No transaction history available.")
        except:
            st.markdown("Transaction details unavailable.")

        # Estimated Values Line Chart with Y-axis starting at the minimum value
        st.header("Estimated Market Value Over Time")
        try:
            # Extract estimated_values from the data
            estimated_values = data['data']['attributes']['estimated_values']
            
            # Convert the list of dictionaries into a pandas DataFrame
            df_estimated_values = pd.DataFrame(estimated_values)
            
            # Create a 'date' column from 'year' and 'month'
            df_estimated_values['date'] = pd.to_datetime(df_estimated_values[['year', 'month']].assign(day=1))
            
            # Sort the DataFrame by date
            df_estimated_values = df_estimated_values.sort_values('date')
            
            # Reset index to use 'date' in Altair
            df_estimated_values = df_estimated_values.reset_index(drop=True)
            
            # Find the minimum and maximum estimated market values
            min_value = df_estimated_values['estimated_market_value'].min()
            max_value = df_estimated_values['estimated_market_value'].max()
            
            # Optional: Adjust the minimum value slightly lower for better visualization
            y_axis_min = min_value * 0.98  # Adjust as needed
            
            # Plot using Altair with custom y-axis range
            chart = alt.Chart(df_estimated_values).mark_line().encode(
                x=alt.X('date:T', title='Date'),
                y=alt.Y('estimated_market_value:Q',
                        title='Estimated Market Value (£)',
                        scale=alt.Scale(domain=[y_axis_min, max_value]))
            ).properties(
                title='Estimated Market Value Over Time'
            ).interactive()  # Enable zooming and panning
            
            st.altair_chart(chart, use_container_width=True)
        except:
            st.markdown("Estimated market value data unavailable.")


        # Energy Performance
        st.header("Energy Performance")
        try:
            col1, col2 = st.columns(2)
            with col1:
                st.subheader("EPC Details")
                st.markdown(f"**Current Rating:** {data['data']['attributes']['energy_performance']['energy_efficiency']['current_rating']}")
                st.markdown(f"**Potential Rating:** {data['data']['attributes']['energy_performance']['energy_efficiency']['potential_rating']}")
                st.markdown(f"**Environmental Impact:** {data['data']['attributes']['energy_performance']['environmental_impact']['current_impact']}")
            with col2:
                st.subheader("Energy Efficiency")
                st.markdown(f"**Efficiency Percentage:** {data['data']['attributes']['energy_performance']['energy_efficiency']['current_efficiency']}%")
                st.markdown(f"**Potential Efficiency:** {data['data']['attributes']['energy_performance']['energy_efficiency']['potential_efficiency']}%")
        except:
            st.markdown("Energy performance details unavailable.")

        # Estimated Values
        st.header("Property Value Estimates")
        try:
            col1, col2 = st.columns(2)
            with col1:
                st.subheader("Current Estimate")
                st.markdown(f"**Estimated Market Value:** £{data['data']['attributes']['estimated_values'][0]['estimated_market_value']}")
                st.markdown(f"**Estimated Rental Value:** £{data['data']['attributes']['estimated_rental_value']['estimated_monthly_rental_value']} per month")
            with col2:
                st.subheader("Annual Yield")
                st.markdown(f"**Annual Rental Yield:** {data['data']['attributes']['estimated_rental_value']['estimated_annual_rental_yield']}%")
        except:
            st.markdown("Property value estimates unavailable.")

        # Map Section
        st.header("Property Map")
        try:
            import pandas as pd  # Ensure pandas is imported
            
            # Extract polygon coordinates
            polygons = data['data']['attributes']['title_deeds']['titles'][0]['polygons']
            # Assuming we use the first polygon
            epsg_4326_polygon = polygons[0]['epsg_4326_polygon']
            coordinates = epsg_4326_polygon['coordinates'][0]  # Get the first (and usually only) polygon

            # Extract property location (add this to mark the house location)
            property_location = data['data']['attributes']['location']['coordinates']
            property_lat = property_location['latitude']
            property_lon = property_location['longitude']

            # Extract education data
            education_data = data['data']['attributes']['education']

            # Combine all schools into a single list
            school_categories = ['nursery', 'primary', 'secondary', 'post_16', 'all_through', 'pupil_referral_units', 'special', 'independent']
            schools = []
            for category in school_categories:
                if category in education_data:
                    for school in education_data[category]:
                        school_info = {
                            'name': school.get('name', 'Unknown'),
                            'latitude': school['location']['coordinates']['latitude'],
                            'longitude': school['location']['coordinates']['longitude'],
                            'types': ', '.join(school.get('school_types', [])),
                            'distance_in_metres': school.get('distance_in_metres', 0)
                        }
                        schools.append(school_info)

            # Create a DataFrame for schools
            df_schools = pd.DataFrame(schools)

            # Compute combined coordinates for bounding box (property polygon, schools, and property location)
            all_lats = [coord[1] for coord in coordinates]  # Polygon latitudes
            all_lons = [coord[0] for coord in coordinates]  # Polygon longitudes

            all_lats += df_schools['latitude'].tolist()  # Add school latitudes
            all_lons += df_schools['longitude'].tolist()  # Add school longitudes

            all_lats.append(property_lat)  # Add property latitude
            all_lons.append(property_lon)  # Add property longitude

            # Compute bounds
            min_lat = min(all_lats)
            max_lat = max(all_lats)
            min_lon = min(all_lons)
            max_lon = max(all_lons)

            # Compute center of all features
            center_lat = (min_lat + max_lat) / 2
            center_lon = (min_lon + max_lon) / 2

            # Compute zoom level
            lat_diff = max_lat - min_lat
            lon_diff = max_lon - min_lon
            zoom = 12  # Starting zoom level; adjust as needed

            # Adjust zoom based on the extent of the data
            max_extent = max(lat_diff, lon_diff)
            if max_extent < 0.01:
                zoom = 15
            elif max_extent < 0.05:
                zoom = 14
            elif max_extent < 0.1:
                zoom = 13
            else:
                zoom = 12

            # Create a PyDeck layer for the polygon
            polygon_layer = pdk.Layer(
                'PolygonLayer',
                data=[{
                    'path': coordinates,  # List of [lon, lat]
                    'name': 'Property Boundary'
                }],
                get_polygon='path',
                pickable=True,
                stroked=True,
                filled=True,
                extruded=False,
                wireframe=True,
                get_fill_color='[255, 0, 0, 100]',
                get_line_color='[255, 0, 0, 255]',
            )

            # Create a ScatterplotLayer for schools
            schools_layer = pdk.Layer(
                'ScatterplotLayer',
                data=df_schools,
                get_position='[longitude, latitude]',
                get_radius=100,  # Adjust the radius size as needed
                get_fill_color='[0, 0, 255, 160]',  # Blue color with transparency
                pickable=True,
                auto_highlight=True,
            )

            # Create a ScatterplotLayer for the property location (red dot)
            house_layer = pdk.Layer(
                'ScatterplotLayer',
                data=[{'latitude': property_lat, 'longitude': property_lon}],
                get_position='[longitude, latitude]',
                get_radius=150,  # Adjust the radius size as needed
                get_fill_color='[255, 0, 0, 255]',  # Red color
                pickable=False,
            )

            # Update tooltip to include school info
            tooltip = {
                "html": "<b>{name}</b><br/>Type: {types}<br/>Distance: {distance_in_metres}m",
                "style": {
                    "backgroundColor": "steelblue",
                    "color": "white"
                }
            }

            view_state = pdk.ViewState(
                longitude=center_lon,
                latitude=center_lat,
                zoom=zoom,
                pitch=0,
            )

            # Update the Deck to include the new house_layer
            r = pdk.Deck(
                layers=[polygon_layer, schools_layer, house_layer],
                initial_view_state=view_state,
                tooltip=tooltip
            )

            # Render the map with the schools and house location included
            st.pydeck_chart(r)

        except:
            st.markdown("Map data unavailable.")

        # Market Statistics Section
        st.header("Market Statistics")

        try:
            # Extract market statistics data
            market_stats = data['data']['attributes']['market_statistics']['outcode']
            
            # Create tabs for the two charts
            tab1, tab2 = st.tabs(["Monthly Sales and Average Price", "Sales by Price Bracket"])
            
            with tab1:
                # Prepare data for the first chart
                sales_monthly = market_stats['sales_monthly']
                df_sales_monthly = pd.DataFrame(sales_monthly)
                
                # Create a 'date' column from 'year' and 'month'
                df_sales_monthly['date'] = pd.to_datetime(df_sales_monthly[['year', 'month']].assign(day=1))
                
                # Sort the DataFrame by date
                df_sales_monthly = df_sales_monthly.sort_values('date')
                
                # Create base chart
                base = alt.Chart(df_sales_monthly).encode(
                    x=alt.X('date:T', title='Date')
                )
                
                # Line chart for average price
                line = base.mark_line(color='blue', strokeWidth=3).encode(
                    y=alt.Y('average_price:Q', axis=alt.Axis(title='Average Price (£)'), scale=alt.Scale(zero=False)),
                    tooltip=[alt.Tooltip('date:T', title='Date'),
                            alt.Tooltip('average_price:Q', title='Average Price (£)', format=',')]
                )
                
                # Bar chart for count of sales
                bar = base.mark_bar(color='orange', opacity=0.6).encode(
                    y=alt.Y('count_of_sales:Q', axis=alt.Axis(title='Count of Sales')),
                    tooltip=[alt.Tooltip('date:T', title='Date'),
                            alt.Tooltip('count_of_sales:Q', title='Count of Sales')]
                )
                
                # Layer the charts and use dual y-axes
                chart = alt.layer(
                    bar,
                    line.encode(y=alt.Y('average_price:Q', axis=alt.Axis(title='Average Price (£)', orient='right'), scale=alt.Scale(zero=False)))
                ).resolve_scale(
                    y='independent'  # Use independent scales for y-axes
                ).properties(
                    width=700,
                    height=400,
                    title='Monthly Sales and Average Price'
                ).interactive()

                st.altair_chart(chart, use_container_width=True)
            
            with tab2:
                # Prepare data for the second chart
                sales_price_bracket = market_stats['sales_price_bracket']
                df_price_bracket = pd.DataFrame(sales_price_bracket)
                
                # Create the chart
                bar_chart = alt.Chart(df_price_bracket).mark_bar(color='teal').encode(
                    x=alt.X('price_bracket_name:N', sort='ascending', title='Price Bracket'),
                    y=alt.Y('count_of_sales:Q', title='Count of Sales'),
                    tooltip=[
                        alt.Tooltip('price_bracket_name:N', title='Price Bracket'),
                        alt.Tooltip('count_of_sales:Q', title='Count of Sales')
                    ]
                ).properties(
                    width=700,
                    height=400,
                    title='Sales by Price Bracket'
                ).configure_axisX(
                    labelAngle=-45  # Rotate x-axis labels for better readability
                )
                
                st.altair_chart(bar_chart, use_container_width=True)
                
        except:
            st.markdown("Market statistics data unavailable.")
        except Exception as e:
            st.markdown(f"An error occurred while plotting market statistics: {str(e)}")

        st.header("Nearby Listings")
        tab1, tab2 = st.tabs(["Completed Listings", "Sale Listings"])

        with tab2:
            try:
                sale_listings = data['data']['attributes']['nearby_completed_transactions']
                if sale_listings:
                    num_cols = 3
                    cols = st.columns(num_cols)
                    for idx, listing in enumerate(sale_listings[:9]):
                        col = cols[idx % num_cols]
                        with col:
                            address = listing['address']['royal_mail_format'].get('thoroughfare', 'N/A')
                            listing_type = listing.get('listing_type', 'N/A').capitalize()
                            listed_date = listing.get('listed_date', 'N/A')
                            number_of_bedrooms = listing.get('number_of_bedrooms', 'N/A')
                            status = listing.get('status', 'N/A')
                            price = listing.get('price', 'N/A')

                            st.markdown(f"**Address:** {address}")
                            st.markdown(f"**Listing Type:** {listing_type}")
                            st.markdown(f"**Listed Date:** {listed_date}")
                            st.markdown(f"**Bedrooms:** {number_of_bedrooms}")
                            st.markdown(f"**Status:** {status}")
                            st.markdown(f"**Price:** £{price:,}")
                            st.markdown("---")
                else:
                    st.write("No nearby sale listings available.")
            except KeyError:
                st.markdown("Nearby listings data unavailable.")
            except Exception as e:
                st.markdown(f"An error occurred while displaying nearby listings: {str(e)}")

        with tab1:
            try:
                sale_listings = data['data']['attributes']['nearby_listings']['sale_listings']
                if sale_listings:
                    num_cols = 3
                    cols = st.columns(num_cols)
                    for idx, listing in enumerate(sale_listings[:9]):
                        col = cols[idx % num_cols]
                        with col:
                            address = listing['address']['royal_mail_format'].get('thoroughfare', 'N/A')
                            listing_type = listing.get('listing_type', 'N/A').capitalize()
                            listed_date = listing.get('listed_date', 'N/A')
                            number_of_bedrooms = listing.get('number_of_bedrooms', 'N/A')
                            status = listing.get('status', 'N/A')
                            price = listing.get('price', 'N/A')
                            main_image_url = listing.get('main_image_url', None)

                            if main_image_url:
                                st.image(main_image_url, use_container_width='always')
                            else:
                                st.write("No image available")

                            st.markdown(f"**Address:** {address}")
                            st.markdown(f"**Listing Type:** {listing_type}")
                            st.markdown(f"**Listed Date:** {listed_date}")
                            st.markdown(f"**Bedrooms:** {number_of_bedrooms}")
                            st.markdown(f"**Status:** {status}")
                            st.markdown(f"**Price:** £{price:,}")
                            st.markdown("---")
                else:
                    st.write("No nearby sale listings available.")
            except KeyError:
                st.markdown("Nearby listings data unavailable.")
            except Exception as e:
                st.markdown(f"An error occurred while displaying nearby listings: {str(e)}")


    except Exception as e:
        st.markdown(f"An error occurred: {str(e)}")
        st.markdown("Please ensure results.json exists in the same directory.")
