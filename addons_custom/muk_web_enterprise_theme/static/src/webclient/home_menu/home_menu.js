import { user } from "@web/core/user";
import { url } from "@web/core/utils/urls";
import { patch } from "@web/core/utils/patch";
import { cookie } from "@web/core/browser/cookie";

import { HomeMenu } from "@web_enterprise/webclient/home_menu/home_menu";

patch(HomeMenu.prototype, {
    setup() {
        super.setup();
        if (
    		cookie.get("color_scheme") == "dark" &&
    		user.activeCompany.has_background_image_dark 
    	) {
        	this.backgroundImageUrl = url('/web/image', {
                model: 'res.company',
                field: 'background_image_dark',
                id: user.activeCompany.id,
            });
        } else if (
            cookie.get("color_scheme") != "dark" &&
        	user.activeCompany.has_background_image_light
        ) {
        	this.backgroundImageUrl = url('/web/image', {
                model: 'res.company',
                field: 'background_image_light',
                id: user.activeCompany.id,
            });
        }
    },
});
